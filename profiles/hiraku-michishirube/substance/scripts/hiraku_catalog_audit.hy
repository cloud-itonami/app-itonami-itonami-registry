#!/usr/bin/env hy
"hiraku-michishirube: measure the 道しるべ catalog.\n\nReads data/catalog.json + data/axes.json from the ao-hiraku checkout, probes the\nlinks that were checked longest ago, and reports coverage per (axis, stage).\nEmits MEASURE<TAB>key<TAB>value and GAP<TAB>axis<TAB>stage<TAB>alive<TAB>total\nlines, appends one row to workspace/michishirube-ledger.jsonl.\n\nWrites only inside the profile workspace. The catalog itself is never edited\nhere; changes are proposals (workspace/proposals/*.json) for the operator.\n"
(import json os sys time urllib.request urllib.error)
(setv PROFILE ((getattr (getattr os "path") "dirname") ((getattr (getattr os "path") "dirname") ((getattr (getattr os "path") "abspath") __file__))))
(setv WS ((getattr (getattr os "path") "join") PROFILE "workspace"))
(setv LEDGER ((getattr (getattr os "path") "join") WS "michishirube-ledger.jsonl"))
(setv LINK_STATE ((getattr (getattr os "path") "join") WS "link-state.json"))
(defn _find_repo []
  "Where data/ lives: $HIRAKU_REPO, the ao-hiraku checkout, else the copy\n    bundled in the profile itself (how a peer node that runs this bot by\n    bundle CID, without the checkout, gets the catalog)."
  (setv here ((getattr (getattr os "path") "dirname") ((getattr (getattr os "path") "dirname") ((getattr (getattr os "path") "abspath") __file__))))
  (for [c (tuple [((getattr (getattr os "environ") "get") "HIRAKU_REPO") "~/github/cloud-itonami/ao-hiraku" here])]
    (if (and c ((getattr (getattr os "path") "isfile") ((getattr (getattr os "path") "join") ((getattr (getattr os "path") "expanduser") c) "data" "catalog.json")))
      (do (return ((getattr (getattr os "path") "expanduser") c)))
      None
    )
  )
  (return here)
)
(setv REPO (_find_repo))
(setv PROBES_PER_TICK (min 10 (max 0 (int ((getattr (getattr os "environ") "get") "HIRAKU_PROBES" "10")))))
(setv RECHECK_SECONDS (* (* 7 24) 3600))
(setv UA "Mozilla/5.0 (compatible; itonami-hiraku-linkcheck/0.1; +https://itonami.cloud)")
((getattr os "makedirs") ((getattr (getattr os "path") "join") WS "proposals") :exist_ok True)
(defn m [k v] (print (% "MEASURE\t%s\t%s" (tuple [k v]))))
(defn load [name] (with [f (open ((getattr (getattr os "path") "join") REPO "data" name) :encoding "utf-8")] (return ((getattr json "load") f))))
(defn probe [url]
  "Return (status, detail). status: alive | dead | error."
  (for [method (tuple ["HEAD" "GET"])]
    (setv req ((getattr (getattr urllib "request") "Request") url :method method :headers {"User-Agent" UA}))
    (try
      (with [r ((getattr (getattr urllib "request") "urlopen") req :timeout 12)] (return (tuple ["alive" (% "%s %d" (tuple [method (getattr r "status")]))])))
      (except [e (getattr (getattr urllib "error") "HTTPError")]
        (if (and (= method "HEAD") (in (getattr e "code") (tuple [403 405 501])))
          (do (continue))
          None
        )
        (return (tuple [(if (in (getattr e "code") (tuple [404 410])) "dead" "error") (% "%s %d" (tuple [method (getattr e "code")]))]))
      )
      (except [e Exception] (return (tuple ["error" (% "%s %s" (tuple [method (getattr (type e) "__name__")]))])))
    )
  )
  (return (tuple ["error" "no-method"]))
)
(try
  (setv axes (load "axes.json"))
  (setv catalog (load "catalog.json"))
  (except [e Exception]
    (m "catalog" (% "UNMEASURED %s" (getattr (type e) "__name__")))
    ((getattr sys "exit") 1)
  )
)
(setv entries (get catalog "entries"))
(try
  (with [f (open LINK_STATE :encoding "utf-8")] (setv state ((getattr json "load") f)))
  (except [FileNotFoundError] (setv state {}))
  (except [e Exception]
    (m "link-state" (% "UNMEASURED %s" (getattr (type e) "__name__")))
    ((getattr sys "exit") 1)
  )
)
(if (not (isinstance state dict))
  (do
    (m "link-state" "UNMEASURED invalid-shape")
    ((getattr sys "exit") 1)
  )
  None
)
(setv now ((getattr time "time")))
(setv due (lfor e entries :if (and ((getattr e "get") "url") (> (- now ((getattr ((getattr state "get") (get e "id") {}) "get") "ts" 0)) RECHECK_SECONDS)) e))
((getattr due "sort") :key (fn [e] ((getattr ((getattr state "get") (get e "id") {}) "get") "ts" 0)))
(setv probed [])
(for [e (cut due None PROBES_PER_TICK)]
  (setv [status detail] (probe (get e "url")))
  (setv (get state (get e "id")) {"ts" now "status" status "detail" detail "url" (get e "url")})
  ((getattr probed "append") (tuple [(get e "id") status detail]))
  (print (% "PROBE\t%s\t%s\t%s" (tuple [(get e "id") status detail])))
)
(with [f (open LINK_STATE "w" :encoding "utf-8")] ((getattr json "dump") state f :ensure_ascii False :indent 1))
(defn alive [e]
  (if (not ((getattr e "get") "url"))
    (do (return (bool ((getattr e "get") "phone"))))
    None
  )
  (return (= ((getattr ((getattr state "get") (get e "id") {}) "get") "status") "alive"))
)
(setv cells [])
(for [a (get axes "axes")]
  (for [s (get axes "stages")]
    (setv inside (lfor e entries :if (and (in (get a "id") (get e "axes")) (in (get s "id") (get e "stages"))) e))
    ((getattr cells "append") {"axis" (get a "id") "stage" (get s "id") "total" (len inside) "alive" (sum (gfor e inside :if (alive e) 1))})
  )
)
(setv with_url (lfor e entries :if ((getattr e "get") "url") e))
(setv measured (lfor e with_url :if (in (get e "id") state) e))
(setv alive_n (sum (gfor e with_url :if (= ((getattr ((getattr state "get") (get e "id") {}) "get") "status") "alive") 1)))
(setv dead (sorted (gfor e with_url :if (= ((getattr ((getattr state "get") (get e "id") {}) "get") "status") "dead") (get e "id"))))
(setv errs (sorted (gfor e with_url :if (= ((getattr ((getattr state "get") (get e "id") {}) "get") "status") "error") (get e "id"))))
(m "entries" (len entries))
(m "links-measured" (% "%d/%d" (tuple [(len measured) (len with_url)])))
(m "links-alive" (if measured alive_n "UNMEASURED"))
(m "links-dead" (or ((getattr "," "join") dead) "none"))
(m "links-error" (or ((getattr "," "join") errs) "none"))
(m "cells" (len cells))
(m "cells-empty" (sum (gfor c cells :if (= (get c "total") 0) 1)))
(m "cells-no-alive" (sum (gfor c cells :if (= (get c "alive") 0) 1)))
(m "free-ratio" (% "%.2f" (/ (sum (gfor e entries :if (= ((getattr e "get") "cost") "free") 1)) (max 1 (len entries)))))
(setv langs (sorted (sfor e entries l ((getattr e "get") "langs" []) l)))
(m "langs-covered" ((getattr "," "join") langs))
(m "langs-missing" (or ((getattr "," "join") (gfor l (get axes "languages") :if (not (in l langs)) l)) "none"))
((getattr cells "sort") :key (fn [c] (tuple [(get c "alive") (get c "total") (get c "axis") (get c "stage")])))
(for [c (cut cells None 8)] (print (% "GAP\t%s\t%s\t%d\t%d" (tuple [(get c "axis") (get c "stage") (get c "alive") (get c "total")]))))
(setv row {"ts" ((getattr time "strftime") "%Y-%m-%dT%H:%M:%S%z") "entries" (len entries) "links_measured" (len measured) "links_with_url" (len with_url) "links_alive" alive_n "dead" dead "error" errs "probed" probed "cells_empty" (sum (gfor c cells :if (= (get c "total") 0) 1)) "cells_no_alive" (sum (gfor c cells :if (= (get c "alive") 0) 1)) "weakest" (cut cells None 3)})
(with [f (open LEDGER "a" :encoding "utf-8")] ((getattr f "write") (+ ((getattr json "dumps") row :ensure_ascii False) "\n")))
