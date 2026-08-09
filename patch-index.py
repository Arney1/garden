"""
patch-index.py
Injects custom additions into Logseq's exported index.html.
Idempotent — safe to run multiple times; skips if already patched.

Usage: python3 patch-index.py [path/to/index.html]
"""

import re
import sys
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

INDEX_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "index.html"

SENTINEL    = 'id="loading"'          # presence = already patched
LANDING     = 'Arney%20Nova'          # URL-encoded landing page name
OG_TITLE    = 'Arney Nova - Digital Garden'
OG_DESC     = 'a personal, evolving space for notes, ideas, and experiments. a place where pieces of knowledge intertwine, forming an interconnected web of information.'

# ── Snippet builders ──────────────────────────────────────────────────────────

def route_redirect():
    return f"""<!-- default route redirect -->
    <script>
    if (!location.hash ||
        location.hash === '#/' ||
        location.hash === '#/page/' ||
        location.hash === '#/page') {{
      location.replace('#/page/{LANDING}');
    }}
    </script>"""


def multi_tab_guard():
    return """ <!-- multi-tab guard and isolation -->
 <script>
     window.addEventListener('storage', function(e) {
       e.stopImmediatePropagation();
     }, true);

     if ('locks' in navigator) {
       navigator.locks.request('logseq_publish_lock', { ifAvailable: true }, async (lock) => {
         if (!lock) {
           window.stop();
           const showFallback = () => {
             document.body.innerHTML = `
               <div id="tab-alert-screen">
                 <div class="tab-alert-content">
                   <svg class="tab-alert-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                     <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2"></path>
                   </svg>
                   <h2 class="tab-alert-title">already open in another tab</h2>
                   <p class="tab-alert-desc">this digital garden is currently active elsewhere. please switch to your open tab to continue reading.</p>
                 </div>
               </div>`;
           };
           if (document.readyState === 'loading') {
             document.addEventListener('DOMContentLoaded', showFallback);
           } else {
             showFallback();
           }
         } else {
           await new Promise(() => {});
         }
       });
     }
   </script>"""


def preload_hints(wasm_file):
    return f"""   <link rel="preload" href="static/js/main.js" as="script">
     <link rel="preload" href="static/js/ui.js" as="script">
     <link rel="preload" href="static/js/{wasm_file}" as="fetch" crossorigin>
     <link rel="preload" href="static/img/logo.png" as="image">"""


def loading_styles():
    return """   <style>
     :root {
       --bg-dark: #16171a;
       --accent-color: #6366f1;
       --text-main: #e1e7ef;
       --text-muted: #8b949e;
       --font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
     }

     #loading {
       position: fixed;
       bottom: 32px;
       left: 50%;
       transform: translateX(-50%);
       display: flex;
       align-items: center;
       justify-content: center;
       background: var(--bg-dark);
       padding: 16px 24px;
       border: 1px solid rgba(255, 255, 255, 0.08);
       border-radius: 16px;
       box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
       z-index: 99;
       opacity: 1;
       visibility: visible;
       transition: opacity 0.4s ease-out, visibility 0.4s ease-out, transform 0.4s ease-out;
       will-change: opacity, visibility, transform;
       width: max-content;
       max-width: 90vw;
     }

     #loading.fade-out {
       opacity: 0;
       visibility: hidden;
       transform: translate(-50%, 20px);
     }

     .loader-content {
       display: flex;
       flex-direction: row;
       align-items: center;
       gap: 16px;
     }

     .loader-avatar {
       width: 40px;
       height: 40px;
       border-radius: 10px;
       box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
       animation: loader-pulse 2.2s infinite ease-in-out;
       will-change: transform, filter;
       transform: translateZ(0);
     }

     .loader-info {
       display: flex;
       flex-direction: column;
       gap: 8px;
     }

     .loader-text-row {
       display: flex;
       gap: 6px;
       align-items: center;
       font-family: var(--font-family);
       font-size: 13px;
       font-weight: 400;
       color: var(--text-muted);
       letter-spacing: 0.04em;
       text-transform: lowercase;
     }

     .loader-time {
       color: var(--accent-color);
       font-variant-numeric: tabular-nums;
     }

     .loader-bar {
       width: 140px;
       height: 3px;
       background: rgba(255, 255, 255, 0.06);
       border-radius: 3px;
       overflow: hidden;
       position: relative;
     }

     .loader-progress {
       position: absolute;
       top: 0;
       left: 0;
       bottom: 0;
       width: 0%;
       background: var(--accent-color);
       border-radius: 3px;
       transition: width 0.15s ease-out;
       will-change: width;
       transform: translateZ(0);
     }

     #tab-alert-screen {
       position: fixed;
       inset: 0;
       display: flex;
       align-items: center;
       justify-content: center;
       background: var(--bg-dark);
       z-index: 99999;
       font-family: var(--font-family);
     }

     .tab-alert-content {
       display: flex;
       flex-direction: column;
       align-items: center;
       text-align: center;
       padding: 2rem;
       max-width: 360px;
     }

     .tab-alert-icon {
       width: 38px;
       height: 38px;
       color: var(--accent-color);
       margin-bottom: 16px;
       opacity: 0.9;
     }

     .tab-alert-title {
       margin: 0 0 8px 0;
       font-size: 1rem;
       font-weight: 500;
       color: var(--text-main);
       letter-spacing: -0.01em;
       text-transform: lowercase;
     }

     .tab-alert-desc {
       margin: 0;
       font-size: 0.85rem;
       color: var(--text-muted);
       line-height: 1.5;
       font-weight: 400;
     }

     @keyframes loader-pulse {
       0%, 100% { transform: scale(1) translateZ(0); opacity: 0.85; }
       50% { transform: scale(1.04) translateZ(0); opacity: 1; filter: drop-shadow(0 0 10px rgba(99, 102, 241, 0.25)); }
     }
   </style>"""


def loading_html_and_script():
    return """ <div id="loading">
     <div class="loader-content">
       <img src="static/img/logo.png" alt="Avatar" class="loader-avatar" fetchpriority="high" decoding="async">
       <div class="loader-info">
         <div class="loader-text-row">
           <span>entering garden...</span>
           <span class="loader-time" id="loader-time-display">0.0s</span>
         </div>
         <div class="loader-bar">
           <div class="loader-progress" id="loader-progress-bar"></div>
         </div>
       </div>
     </div>
   </div>

   <script>
       (function () {
         const loader = document.getElementById('loading');
         const timeDisplay = document.getElementById('loader-time-display');
         const progressBar = document.getElementById('loader-progress-bar');
         if (!loader) return;

         let dismissed = false;
         let settleTimer = null;
         let startTime = Date.now();
         let simulatedProgress = 0;

         const loadingInterval = setInterval(() => {
           const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
           if (timeDisplay) timeDisplay.innerText = `${elapsed}s`;
           simulatedProgress += (95 - simulatedProgress) * 0.0038;
           if (progressBar) progressBar.style.width = `${simulatedProgress}%`;
         }, 100);

         const dismissLoader = () => {
           if (dismissed) return;
           dismissed = true;
           clearInterval(loadingInterval);
           if (progressBar) progressBar.style.width = '100%';
           setTimeout(() => {
             loader.classList.add('fade-out');
             setTimeout(() => {
               if (loader.parentNode) loader.parentNode.removeChild(loader);
             }, 400);
           }, 150);
         };

         const isReady = () => {
           const container = document.getElementById('main-content-container');
           if (!container) return false;
           if (container.querySelector('.ui__skeleton')) return false;
           if (container.querySelector('.cp__page-inner-wrap')) return true;
           if (container.querySelector('.ls-block')) return true;
           return false;
         };

         const check = () => {
           clearTimeout(settleTimer);
           settleTimer = setTimeout(() => {
             if (isReady()) {
               dismissLoader();
               observer.disconnect();
             }
           }, 80);
         };

         const observer = new MutationObserver(check);
         observer.observe(document.getElementById('root') || document.body, {
           childList: true,
           subtree: true
         });

         check();
       })();
     </script>"""


# ── Patch functions ───────────────────────────────────────────────────────────

def patch(html: str) -> str:
    if SENTINEL in html:
        print("  patch-index: already patched, skipping.")
        return html

    # Detect WASM filename dynamically (it's a content hash, changes on Logseq updates)
    wasm_match = re.search(r'static/js/([a-f0-9]+\.wasm)', html)
    wasm_file = wasm_match.group(1) if wasm_match else '8c42af0b6b628f4fd9b3.wasm'

    # ── 1. After viewport meta: inject route redirect + multi-tab guard + preloads
    viewport_anchor = '<meta content="minimum-scale=1, initial-scale=1, width=device-width, shrink-to-fit=no" name="viewport"></meta>'
    if viewport_anchor not in html:
        print("  patch-index: WARNING — viewport meta not found, skipping head injections.")
    else:
        insertion = (
            viewport_anchor + "\n"
            + route_redirect() + "\n"
            + multi_tab_guard() + "\n"
            + preload_hints(wasm_file)
        )
        html = html.replace(viewport_anchor, insertion, 1)

    # ── 2. Fill OG title
    html = html.replace(
        '<meta property="og:title"></meta>',
        f'<meta property="og:title" content="{OG_TITLE}"></meta>',
        1
    )

    # ── 3. Fill OG description
    html = html.replace(
        '<meta property="og:description"></meta>',
        f'<meta property="og:description" content="{OG_DESC}"></meta>',
        1
    )

    # ── 4. Inject loading styles before </head>
    html = html.replace('</head>', loading_styles() + '\n</head>', 1)

    # ── 5. Inject loading div + script after <div id="root"></div>
    root_div = '<div id="root"></div>'
    if root_div not in html:
        print("  patch-index: WARNING — #root div not found, skipping body injection.")
    else:
        html = html.replace(
            root_div,
            root_div + "\n" + loading_html_and_script(),
            1
        )

    # ── 6. Comment out PDF scripts (unused, ~500KB saved on mobile)
    html = html.replace(
        '<script defer="true" type="module" src="static/js/pdfjs/pdf.mjs"></script>',
        '<!--<script defer="true" type="module" src="static/js/pdfjs/pdf.mjs"></script>-->'
    )
    html = html.replace(
        '<script defer="true" type="module" src="static/js/pdf_viewer3.mjs"></script>',
        '<!--<script defer="true" type="module" src="static/js/pdf_viewer3.mjs"></script>-->'
    )

    return html


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not INDEX_PATH.exists():
        print(f"  patch-index: ERROR — {INDEX_PATH} not found.")
        sys.exit(1)

    original = INDEX_PATH.read_text(encoding='utf-8')
    patched  = patch(original)

    if patched != original:
        INDEX_PATH.write_text(patched, encoding='utf-8')
        print(f"  patch-index: patched {INDEX_PATH}")
    # if already patched, patch() printed the skip message


if __name__ == '__main__':
    main()
