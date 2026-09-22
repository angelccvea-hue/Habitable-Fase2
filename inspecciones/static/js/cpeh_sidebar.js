/* Menú lateral: reforzar toggle y secciones desplegables */
(function () {
  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    // CSS crítico (evita caché vieja del treeview)
    if (!document.getElementById("cpeh-sidebar-tree-css")) {
      var st = document.createElement("style");
      st.id = "cpeh-sidebar-tree-css";
      st.textContent =
        ".app-sidebar .nav-item > .nav-treeview,.main-sidebar .nav-item > .nav-treeview{display:none!important;height:auto!important;max-height:none!important;}" +
        ".app-sidebar .nav-item.menu-open > .nav-treeview,.main-sidebar .nav-item.menu-open > .nav-treeview{display:block!important;height:auto!important;max-height:none!important;overflow:visible!important;}" +
        "body.sidebar-collapse .app-sidebar,body.sidebar-collapse .main-sidebar{margin-left:-250px!important;}";
      document.head.appendChild(st);
    }

    var KEY = "cpeh_sidebar_collapsed";
    var body = document.body;
    if (!body) return;

    try {
      if (localStorage.getItem(KEY) === "1") {
        body.classList.add("sidebar-collapse");
        body.classList.remove("sidebar-open");
      }
    } catch (e) {}

    function persist() {
      try {
        var collapsed = body.classList.contains("sidebar-collapse");
        localStorage.setItem(KEY, collapsed ? "1" : "0");
      } catch (e) {}
    }

    document.addEventListener("click", function (ev) {
      var t = ev.target.closest('[data-lte-toggle="sidebar"], [data-widget="pushmenu"]');
      if (!t) return;
      setTimeout(persist, 50);
    });
  });
})();
