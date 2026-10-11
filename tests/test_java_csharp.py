"""Java and C# in the lite codegraph: regex extraction, never an `exact` edge.

Fixtures live under the OS temporary directory, never inside this repository.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from extract_java_csharp import extract_csharp, extract_java  # noqa: E402
from scan_deps import CODE_SUFFIXES as SCANNED_SUFFIXES  # noqa: E402
from source_state import CODE_SUFFIXES as FRESHNESS_SUFFIXES  # noqa: E402

CONTROLLER = "src/main/java/com/acme/web/OrderController.java"
SERVICE = "src/main/java/com/acme/service/OrderService.java"

JAVA_CONTROLLER = """\
package com.acme.web;

import com.acme.service.OrderService;
import java.util.List;
import static java.util.Collections.emptyList;
import java.util.concurrent.*;

// orderService.fakeCall() inside a comment must not become an edge
@RestController
@RequestMapping("/api")
public class OrderController extends BaseController implements Auditable, Serializable {
    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @GetMapping("/orders")
    public List<Order> list() {
        String note = "orderService.inString() {";
        return orderService.findAll();
    }

    @PostMapping(value = "/orders")
    public Order create(@RequestBody Order order) throws Exception {
        if (order == null) { throw new IllegalStateException("x"); }
        return orderService.save(order);
    }
}

abstract class BaseController {}
"""

JAVA_SERVICE = """\
package com.acme.service;

public interface OrderService {
    List<Order> findAll();
    Order save(Order order);
}
"""

CS_CONTROLLER = """\
using Acme.Services;

namespace Acme.Web
{
    [ApiController]
    [Route("api/[controller]")]
    public class OrdersController : ControllerBase, IAuditable
    {
        private readonly OrderService _service;

        public OrdersController(OrderService service) { _service = service; }

        [HttpGet("orders")]
        public IActionResult List()
        {
            return Ok(_service.GetAll());
        }

        [HttpPost]
        public IActionResult Create(Order order) => Ok(_service.Save(order));
    }
}
"""

CS_SERVICE = """\
namespace Acme.Services
{
    public class OrderService
    {
        public List<Order> GetAll() { return new List<Order>(); }
        public Order Save(Order order) { return order; }
    }
}
"""


class JavaCSharpGraphTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="java-csharp-graph-")
        self.root = Path(self.temp_dir.name) / "project"
        self.root.mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def run_script(self, name: str, *args: str) -> str:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        done = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / name), "--root", str(self.root), *args],
            cwd=str(self.root), env=env, text=True, capture_output=True, check=False,
        )
        self.assertEqual(0, done.returncode, done.stderr)
        return done.stdout

    def build_index(self) -> dict:
        index_path = self.root / "code_index.json"
        self.run_script("build_code_index.py", "--output", str(index_path), "--quiet")
        return json.loads(index_path.read_text(encoding="utf-8"))

    def explore(self, *args: str) -> str:
        return self.run_script("explore.py", "--index", str(self.root / "code_index.json"), *args)

    def edges(self, index: dict, kind: str, source: str, target: str) -> list[dict]:
        return [
            e for e in index["edges"]
            if e["kind"] == kind and e["from"].startswith(source) and e["to"].startswith(target)
        ]

    def test_suffix_lists_still_agree(self) -> None:
        self.assertEqual(set(FRESHNESS_SUFFIXES), SCANNED_SUFFIXES)
        self.assertLessEqual({".java", ".cs"}, SCANNED_SUFFIXES)

    def test_java_graph(self) -> None:
        self.write(CONTROLLER, JAVA_CONTROLLER)
        self.write(SERVICE, JAVA_SERVICE)
        index = self.build_index()

        self.assertEqual("java", index["files"][CONTROLLER]["lang"])
        imports = self.edges(index, "IMPORTS", CONTROLLER, SERVICE)
        self.assertEqual(["heuristic"], [e["conf"] for e in imports])
        # `import static` and `.*` name no single file, so they add no edge.
        self.assertEqual(1, len([e for e in index["edges"] if e["kind"] == "IMPORTS"]))

        calls = self.edges(index, "CALLS", CONTROLLER, f"{SERVICE}::OrderService.findAll")
        self.assertTrue(calls)
        self.assertEqual({"weak"}, {e["conf"] for e in calls})
        self.assertEqual(f"{CONTROLLER}::OrderController.list", calls[0]["from"])
        # Text inside comments and string literals is not code.
        self.assertFalse(self.edges(index, "CALLS", CONTROLLER, f"{SERVICE}::OrderService.fakeCall"))
        self.assertNotIn("inString", json.dumps(index))

        routes = self.explore("--entrypoints")
        self.assertIn("GET /api/orders", routes)
        self.assertIn("POST /api/orders", routes)
        impact = self.explore("--impact", "findAll")
        self.assertIn(CONTROLLER, impact)
        self.assertIn("OrderController.list", impact)

    def test_java_extractor_shapes(self) -> None:
        path = self.write(CONTROLLER, JAVA_CONTROLLER)
        result = extract_java(path, CONTROLLER)
        symbols = result["symbols"]
        self.assertEqual(["BaseController", "Auditable", "Serializable"], symbols["OrderController"]["bases"])
        self.assertEqual("method", symbols["OrderController.<init>"]["kind"])
        self.assertEqual("GET /api/orders", symbols["OrderController.list"]["route"])
        self.assertEqual("POST /api/orders", symbols["OrderController.create"]["route"])
        self.assertEqual(["com.acme.service.OrderService", "java.util.List"], result["imports"])
        for keyword in ("if", "throw", "new"):
            self.assertNotIn(keyword, {c["name"] for c in result["raw_calls"]})

    def test_csharp_graph(self) -> None:
        self.write("Controllers/OrdersController.cs", CS_CONTROLLER)
        self.write("Services/OrderService.cs", CS_SERVICE)
        index = self.build_index()

        self.assertEqual("csharp", index["files"]["Controllers/OrdersController.cs"]["lang"])
        self.assertFalse([e for e in index["edges"] if e["kind"] == "IMPORTS"])
        calls = self.edges(index, "CALLS", "Controllers/OrdersController.cs", "Services/OrderService.cs::OrderService.GetAll")
        self.assertTrue(calls)
        self.assertEqual({"weak"}, {e["conf"] for e in calls})
        self.assertEqual("Controllers/OrdersController.cs::OrdersController.List", calls[0]["from"])

        routes = self.explore("--entrypoints")
        self.assertIn("GET /api/orders/orders", routes)
        self.assertIn("POST /api/orders", routes)  # [controller] token expanded, expression body kept

    def test_csharp_extractor_shapes(self) -> None:
        path = self.write("Controllers/OrdersController.cs", CS_CONTROLLER)
        symbols = extract_csharp(path, "Controllers/OrdersController.cs")["symbols"]
        self.assertEqual(["ControllerBase", "IAuditable"], symbols["OrdersController"]["bases"])
        self.assertIn("OrdersController.<init>", symbols)
        self.assertEqual("class", symbols["OrdersController"]["kind"])
        self.assertNotIn("route", symbols["OrdersController"])

    def test_java_array_annotation_args_keep_the_route(self) -> None:
        source = """\
public class Api {
    @GetMapping({"/a", "/b"})
    public String one() { return ""; }

    @GetMapping("/c") @SuppressWarnings({"unchecked"})
    public String two() { return ""; }

    @PostMapping(path = "/d/{id}")
    public String three() { return ""; }
}
"""
        symbols = extract_java(self.write("Api.java", source), "Api.java")["symbols"]
        self.assertEqual("GET /a", symbols["Api.one"]["route"])  # first path of an array
        self.assertEqual("GET /c", symbols["Api.two"]["route"])
        self.assertEqual("POST /d/{id}", symbols["Api.three"]["route"])

    def test_generic_method_calls_are_recorded(self) -> None:
        cs = "class A { void Run() { var w = _svc.Load<Widget>(id); GetAll<Order>(); sc.AddScoped<I, T>(); } }"
        found = extract_csharp(self.write("A.cs", cs), "A.cs")["raw_calls"]
        self.assertEqual({"Load", "GetAll", "AddScoped"}, {c["name"] for c in found})
        java = "class B { void run() { Collections.<String>emptyList(); svc.<T>load(1); load<T>(2); } }"
        names = {c["name"] for c in extract_java(self.write("B.java", java), "B.java")["raw_calls"]}
        self.assertIn("load", names)

    def test_comparison_is_not_a_generic_call(self) -> None:
        cs = "class A { bool Run(int i, int n, int k, int x) { return i < n && k > (x); } }"
        found = extract_csharp(self.write("A.cs", cs), "A.cs")["raw_calls"]
        self.assertEqual([], found)

    def test_calls_to_project_methods_named_like_library_calls_resolve(self) -> None:
        self.write("Store.java", "class Store { Object get(int id) { return null; } }")
        self.write("Handler.java", "class Handler { void run() { store.get(1); System.out.println(1); } }")
        self.write("Repo.cs", "class Repo { void Add(int x) { } }")
        self.write("Svc.cs", "class Svc { void Run() { _repo.Add(1); Console.WriteLine(1); } }")
        index = self.build_index()
        java = {e["to"] for e in self.edges(index, "CALLS", "Handler.java", "")}
        self.assertEqual({"Store.java::Store.get"}, java)  # println has no project definition
        cs = {e["to"] for e in self.edges(index, "CALLS", "Svc.cs", "")}
        self.assertEqual({"Repo.cs::Repo.Add"}, cs)
        self.assertIn("Handler.run", self.explore("--impact", "get"))

    def test_route_from_a_constant_is_unresolved_not_root(self) -> None:
        java = """class Api {
    static final String PATH = "/orders";
    @GetMapping(PATH)
    String a() { return ""; }
    @PostMapping(path = PATH)
    String b() { return ""; }
    @GetMapping
    String c() { return ""; }
    @GetMapping(produces = "x")
    String d() { return ""; }
}
"""
        symbols = extract_java(self.write("Api.java", java), "Api.java")["symbols"]
        self.assertEqual("GET <unresolved:PATH>", symbols["Api.a"]["route"])
        self.assertEqual("POST <unresolved:PATH>", symbols["Api.b"]["route"])
        self.assertEqual("GET /", symbols["Api.c"]["route"])
        self.assertEqual("GET /", symbols["Api.d"]["route"])
        cs = """class OrdersController {
    const string Path = "/orders";
    [HttpGet(Path)]
    public int A() => 1;
    [HttpGet]
    public int B() => 2;
    [HttpDelete(Name = "x")]
    public int C() => 3;
}
"""
        symbols = extract_csharp(self.write("O.cs", cs), "O.cs")["symbols"]
        self.assertEqual("GET <unresolved:Path>", symbols["OrdersController.A"]["route"])
        self.assertEqual("GET /", symbols["OrdersController.B"]["route"])
        self.assertEqual("DELETE /", symbols["OrdersController.C"]["route"])

    def test_route_is_a_literal_only_when_the_whole_expression_is_one(self) -> None:
        java = """class Api {
    @GetMapping("/api" + SUFFIX)
    String a() { return ""; }
    @GetMapping(value = "/api" + SUFFIX, produces = "x")
    String b() { return ""; }
    @GetMapping({"/x", "/y"})
    String c() { return ""; }
}
"""
        symbols = extract_java(self.write("Api.java", java), "Api.java")["symbols"]
        self.assertEqual('GET <unresolved:"/api" + SUFFIX>', symbols["Api.a"]["route"])
        self.assertEqual('GET <unresolved:"/api" + SUFFIX>', symbols["Api.b"]["route"])
        self.assertEqual("GET /x", symbols["Api.c"]["route"])
        cs = """class OrdersController {
    [HttpGet("/api" + Suffix)]
    public int A() => 1;
    [HttpGet(@"/orders")]
    public int B() => 2;
}
"""
        symbols = extract_csharp(self.write("O.cs", cs), "O.cs")["symbols"]
        self.assertEqual('GET <unresolved:"/api" + Suffix>', symbols["OrdersController.A"]["route"])
        self.assertEqual("GET /orders", symbols["OrdersController.B"]["route"])

    def test_absolute_csharp_action_route_ignores_an_unresolved_prefix(self) -> None:
        cs = """[Route(PREFIX)]
class Api {
    const string PREFIX = "api";
    [HttpGet("/health")]
    public int Health() => 1;
    [HttpGet("~/ready")]
    public int Ready() => 1;
    [HttpGet("items")]
    public int Items() => 1;
}
"""
        symbols = extract_csharp(self.write("Api.cs", cs), "Api.cs")["symbols"]
        self.assertEqual("GET /health", symbols["Api.Health"]["route"])
        self.assertEqual("GET /ready", symbols["Api.Ready"]["route"])
        self.assertEqual("GET <unresolved:PREFIX>", symbols["Api.Items"]["route"])

    def test_nested_generic_calls_are_recorded(self) -> None:
        cs = "class A { void Run() { var w = _svc.Load<List<Widget>>(id); var m = Map<string, List<int>>(); } }"
        found = extract_csharp(self.write("A.cs", cs), "A.cs")["raw_calls"]
        self.assertEqual({"Load", "Map"}, {c["name"] for c in found})

    def test_no_java_or_csharp_edge_is_ever_exact(self) -> None:
        self.write(CONTROLLER, JAVA_CONTROLLER)
        self.write(SERVICE, JAVA_SERVICE)
        self.write("Controllers/OrdersController.cs", CS_CONTROLLER)
        self.write("Services/OrderService.cs", CS_SERVICE)
        index = self.build_index()
        regex_files = {rel for rel, info in index["files"].items() if info["lang"] in {"java", "csharp"}}
        self.assertEqual(4, len(regex_files))
        self.assertTrue(any(e["kind"] == "EXTENDS" for e in index["edges"]))
        for edge in index["edges"]:
            self.assertIn(edge["from"].split("::")[0], regex_files)
            self.assertNotEqual("exact", edge["conf"], edge)
            if edge["kind"] == "CALLS":
                self.assertEqual("weak", edge["conf"], edge)

    def test_build_output_folders_are_skipped(self) -> None:
        self.write("obj/Debug/Generated.cs", "class Generated { void Run() {} }")
        self.write(".gradle/Cache.java", "class Cache { void run() {} }")
        self.write("src/Real.cs", "class Real { void Run() {} }")
        self.assertEqual(["src/Real.cs"], sorted(self.build_index()["files"]))


if __name__ == "__main__":
    unittest.main()
