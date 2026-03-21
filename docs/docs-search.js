/**
 * Client-side documentation search (Fuse.js + search-index.json).
 */
(function () {
    var overlay = document.getElementById("docsSearchOverlay");
    var openBtn = document.getElementById("docsSearchOpen");
    var closeBtn = document.getElementById("docsSearchClose");
    var backdrop = document.getElementById("docsSearchBackdrop");
    var input = document.getElementById("docsSearchInput");
    var resultsEl = document.getElementById("docsSearchResults");
    var emptyEl = document.getElementById("docsSearchEmpty");
    var statusEl = document.getElementById("docsSearchStatus");
    var kbdMod = document.querySelector(".docs-kbd-mod");

    if (!overlay || !openBtn || !input || !resultsEl) {
        return;
    }

    var fuse = null;
    var loadPromise = null;

    function isMacPlatform() {
        return /Mac|iPhone|iPod|iPad/i.test(navigator.platform || "");
    }

    if (kbdMod) {
        kbdMod.textContent = isMacPlatform() ? "⌘" : "Ctrl+";
    }

    function loadIndex() {
        if (loadPromise) {
            return loadPromise;
        }
        loadPromise = fetch("search-index.json")
            .then(function (r) {
                if (!r.ok) {
                    throw new Error("search-index.json");
                }
                return r.json();
            })
            .then(function (data) {
                if (typeof Fuse === "undefined") {
                    throw new Error("Fuse.js not loaded");
                }
                fuse = new Fuse(data, {
                    keys: [
                        { name: "title", weight: 0.38 },
                        { name: "chapter", weight: 0.12 },
                        { name: "text", weight: 0.5 },
                    ],
                    threshold: 0.34,
                    ignoreLocation: true,
                    minMatchCharLength: 2,
                    includeScore: true,
                });
                return fuse;
            })
            .catch(function () {
                statusEl.textContent = "Search index could not be loaded.";
                emptyEl.hidden = false;
                emptyEl.textContent = "Search is unavailable. Try refreshing the page.";
                return null;
            });
        return loadPromise;
    }

    function escapeHtml(s) {
        return String(s)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function snippet(text, q) {
        if (!text || !q.trim()) {
            return escapeHtml(text.slice(0, 140)) + (text.length > 140 ? "…" : "");
        }
        var lower = text.toLowerCase();
        var qi = lower.indexOf(q.trim().toLowerCase().split(/\s+/)[0]);
        if (qi < 0) {
            qi = 0;
        }
        var start = Math.max(0, qi - 40);
        var slice = text.slice(start, start + 160);
        var prefix = start > 0 ? "…" : "";
        return prefix + escapeHtml(slice) + (text.length > start + 160 ? "…" : "");
    }

    function renderResults(items, q) {
        resultsEl.innerHTML = "";
        emptyEl.hidden = true;

        if (!items || items.length === 0) {
            emptyEl.hidden = false;
            statusEl.textContent = q.trim() ? "No results." : "";
            return;
        }

        statusEl.textContent = items.length + " result" + (items.length === 1 ? "" : "s");

        items.slice(0, 12).forEach(function (hit) {
            var item = hit.item;
            var li = document.createElement("li");
            li.setAttribute("role", "none");
            var a = document.createElement("a");
            a.href = item.url;
            a.setAttribute("role", "option");
            a.innerHTML =
                '<span class="docs-search-result-chapter">' +
                escapeHtml(item.chapter) +
                "</span>" +
                '<span class="docs-search-result-title">' +
                escapeHtml(item.title) +
                "</span>" +
                '<span class="docs-search-result-snippet">' +
                snippet(item.text, q) +
                "</span>";
            a.addEventListener("click", function () {
                closeSearch();
            });
            li.appendChild(a);
            resultsEl.appendChild(li);
        });
    }

    function runSearch() {
        var q = input.value;

        if (!fuse) {
            return;
        }

        if (!q.trim()) {
            renderResults([], "");
            return;
        }

        var hits = fuse.search(q, { limit: 12 });
        renderResults(hits, q);
    }

    var searchDebounce = null;
    function onInput() {
        clearTimeout(searchDebounce);
        searchDebounce = setTimeout(runSearch, 120);
    }

    function openSearch() {
        overlay.hidden = false;
        openBtn.setAttribute("aria-expanded", "true");
        document.body.style.overflow = "hidden";

        loadIndex().then(function (f) {
            if (f && input) {
                input.focus();
                input.select();
                runSearch();
            }
        });
    }

    function closeSearch() {
        overlay.hidden = true;
        openBtn.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "";
        input.value = "";
        resultsEl.innerHTML = "";
        emptyEl.hidden = true;
        statusEl.textContent = "";
    }

    openBtn.addEventListener("click", openSearch);
    closeBtn.addEventListener("click", closeSearch);
    backdrop.addEventListener("click", closeSearch);
    input.addEventListener("input", onInput);

    document.addEventListener("keydown", function (e) {
        var mod = isMacPlatform() ? e.metaKey : e.ctrlKey;
        if (mod && (e.key === "k" || e.key === "K")) {
            e.preventDefault();
            if (overlay.hidden) {
                openSearch();
            } else {
                closeSearch();
            }
            return;
        }

        if (e.key === "Escape" && !overlay.hidden) {
            e.preventDefault();
            closeSearch();
            return;
        }

        if (
            e.key === "/" &&
            !overlay.hidden &&
            e.target &&
            (e.target === document.body ||
                e.target.id === "docsContent" ||
                e.target.closest("#docsContent"))
        ) {
            e.preventDefault();
            openSearch();
            return;
        }

        if (
            e.key === "/" &&
            overlay.hidden &&
            e.target &&
            e.target.tagName !== "INPUT" &&
            e.target.tagName !== "TEXTAREA" &&
            !e.target.isContentEditable
        ) {
            e.preventDefault();
            openSearch();
        }
    });

    window.addEventListener("pageshow", function () {
        if (!overlay.hidden) {
            document.body.style.overflow = "hidden";
        }
    });
})();
