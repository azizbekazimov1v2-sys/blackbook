document.addEventListener("DOMContentLoaded", function () {
    document.body.classList.add("page-transition-body", "page-reveal");

    const overlay = document.createElement("div");
    overlay.className = "page-transition-overlay";
    overlay.innerHTML = `
        <div class="page-transition-center">
            <div class="page-transition-logo">Azizbek Azimov</div>
            <div class="page-transition-title">SAT Platform</div>
            <div class="page-transition-sub">Loading your next page...</div>
            <div class="page-transition-bar">
                <div class="page-transition-bar-fill"></div>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    let navigating = false;

    function isSamePage(url) {
        try {
            const current = new URL(window.location.href);
            const next = new URL(url, window.location.origin);
            return current.href === next.href;
        } catch (e) {
            return false;
        }
    }

    function shouldHandleLink(link) {
        if (!link) return false;

        const href = link.getAttribute("href");
        if (!href) return false;
        if (href.startsWith("#")) return false;
        if (href.startsWith("javascript:")) return false;
        if (link.hasAttribute("download")) return false;
        if (link.target === "_blank") return false;

        try {
            const url = new URL(link.href, window.location.origin);
            if (url.origin !== window.location.origin) return false;
        } catch (e) {
            return false;
        }

        return true;
    }

    function startTransition(nextUrl) {
        if (navigating) return;
        navigating = true;

        document.body.classList.add("leaving");
        overlay.classList.add("active");

        setTimeout(() => {
            window.location.href = nextUrl;
        }, 480);
    }

    document.querySelectorAll("a").forEach(link => {
        link.addEventListener("click", function (e) {
            if (!shouldHandleLink(link)) return;

            const nextUrl = link.href;
            if (isSamePage(nextUrl)) return;

            e.preventDefault();
            startTransition(nextUrl);
        });
    });

    window.addEventListener("pageshow", function () {
        document.body.classList.remove("leaving");
        overlay.classList.remove("active");
        navigating = false;
    });
});