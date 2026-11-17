#!/usr/bin/env hy
"hiraku-kyozai: gate pending drafts, then say which material to write next.\n\n1. Every workspace/kyozai/drafts/*.md is checked by the quality gate below.\n   pass -> workspace/kyozai/ready/, fail -> workspace/kyozai/rejected/ (+ .reason).\n2. The next (theme, stage, lang) cell with no ready material is printed as a\n   BRIEF block the agent writes from, with the catalog entries it may cite.\n\nThe gate is the final word: the agent does not re-judge a draft it wrote.\nWrites only inside the profile workspace. Emits MEASURE / GATE / BRIEF lines.\n"
(import glob json os re shutil sys time)
(setv PROFILE ((getattr (getattr os "path") "dirname") ((getattr (getattr os "path") "dirname") ((getattr (getattr os "path") "abspath") __file__))))
(setv WS ((getattr (getattr os "path") "join") PROFILE "workspace"))
(setv KZ ((getattr (getattr os "path") "join") WS "kyozai"))
(setv DIRS (dfor k (tuple ["drafts" "ready" "rejected"]) k ((getattr (getattr os "path") "join") KZ k)))
(setv LEDGER ((getattr (getattr os "path") "join") WS "kyozai-ledger.jsonl"))
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
(setv MAX_REJECTS_PER_CELL 3)
(for [d ((getattr DIRS "values"))] ((getattr os "makedirs") d :exist_ok True))
(defn m [k v] (print (% "MEASURE\t%s\t%s" (tuple [k v]))))
(defn load [name] (with [f (open ((getattr (getattr os "path") "join") REPO "data" name) :encoding "utf-8")] (return ((getattr json "load") f))))
(try
  (setv [axes catalog curriculum safety] (gfor n (tuple ["axes.json" "catalog.json" "curriculum.json" "safety.json"]) (load n)))
  (except [e Exception]
    (m "data" (% "UNMEASURED %s" (getattr (type e) "__name__")))
    ((getattr sys "exit") 1)
  )
)
(setv entries (dfor e (get catalog "entries") (get e "id") e))
(setv known_phones (sfor x (+ (list ((getattr entries "values"))) (get safety "emergency")) ((getattr re "sub") "[^0-9#]" "" ((getattr x "get") "phone" ""))))
((getattr known_phones "discard") "")
(setv known_hosts (set))
(for [x (+ (list ((getattr entries "values"))) (get safety "emergency"))]
  (if ((getattr x "get") "url")
    (do ((getattr known_hosts "add") ((getattr ((getattr re "sub") "^https?://([^/]+).*$" "\\1" (get x "url")) "lower"))))
    None
  )
)
(setv FRONT ((getattr re "compile") "^---\\n(.*?)\\n---\\n" (getattr re "S")))
(defn front_matter [text]
  (setv mt ((getattr FRONT "match") text))
  (if (not mt)
    (do (return {}))
    None
  )
  (setv out {})
  (for [line ((getattr ((getattr mt "group") 1) "splitlines"))]
    (if (in ":" line)
      (do
        (setv [k v] ((getattr line "split") ":" 1))
        (setv (get out ((getattr k "strip"))) ((getattr v "strip")))
      )
      None
    )
  )
  (return out)
)
(defn gate [text]
  "Return list of failure reasons (empty = pass)."
  (setv fails [])
  (setv fm (front_matter text))
  (for [k (tuple ["theme" "stage" "lang" "title"])]
    (if (not ((getattr fm "get") k))
      (do ((getattr fails "append") (% "front-matter-missing:%s" k)))
      None
    )
  )
  (setv body ((getattr FRONT "sub") "" text :count 1))
  (setv n (len body))
  (if (< n 400)
    (do ((getattr fails "append") (% "too-short:%d" n)))
    None
  )
  (if (> n 8000)
    (do ((getattr fails "append") (% "too-long:%d" n)))
    None
  )
  (for [marker (tuple ["<!-- section:manabu -->" "<!-- section:ippo -->" "<!-- section:soudan -->"])]
    (if (not (in marker body))
      (do ((getattr fails "append") (% "section-missing:%s" (cut marker 13 (- 4)))))
      None
    )
  )
  (setv low ((getattr body "lower")))
  (for [p (get safety "banned_phrases")]
    (if (in p body)
      (do ((getattr fails "append") (% "stereotype:%s" p)))
      None
    )
  )
  (for [p (get safety "banned_engagement_tokens")]
    (if (in ((getattr p "lower")) low)
      (do ((getattr fails "append") (% "engagement:%s" p)))
      None
    )
  )
  (for [ph ((getattr re "findall") "(?<![0-9])(?:0\\d{1,4}-\\d{1,4}-\\d{3,4}|#\\d{4}|189|110|119)(?![0-9])" body)]
    (if (not (in ((getattr re "sub") "[^0-9#]" "" ph) known_phones))
      (do ((getattr fails "append") (% "unknown-phone:%s" ph)))
      None
    )
  )
  (for [host ((getattr re "findall") "https?://([^/\\s)>\\]]+)" body)]
    (if (not (in ((getattr host "lower")) known_hosts))
      (do ((getattr fails "append") (% "unknown-host:%s" host)))
      None
    )
  )
  (if (not ((getattr re "search") "https?://|0120-|#8|189" (get ((getattr body "split") "<!-- section:soudan -->") (- 1))))
    (do ((getattr fails "append") "soudan-without-contact"))
    None
  )
  (if (or (in ((getattr fm "get") "lang") (tuple ["ja-easy"])) (= ((getattr fm "get") "stage") "elementary"))
    (do
      (setv sents (lfor s ((getattr re "split") "[。！？\\n]" ((getattr re "sub") "<!--.*?-->|https?://\\S+|[#>*`|\\-]" "" body)) :if (> (len ((getattr s "strip"))) 3) s))
      (if sents
        (do
          (setv avg (/ (sum (gfor s sents (len s))) (len sents)))
          (setv longest (max (gfor s sents (len s))))
          (if (> avg 35)
            (do ((getattr fails "append") (% "easy-avg-sentence:%.0f" avg)))
            None
          )
          (if (> longest 80)
            (do ((getattr fails "append") (% "easy-long-sentence:%d" longest)))
            None
          )
        )
        None
      )
    )
    None
  )
  (return (tuple [fails fm]))
)
(defn cell_key [fm] (return (% "%s|%s|%s" (tuple [((getattr fm "get") "theme") ((getattr fm "get") "stage") ((getattr fm "get") "lang")]))))
(do (setv _kotoba_assign_32 0) (setv passed _kotoba_assign_32) (setv failed _kotoba_assign_32))
(for [path (sorted ((getattr glob "glob") ((getattr (getattr os "path") "join") (get DIRS "drafts") "*.md")))]
  (setv name ((getattr (getattr os "path") "basename") path))
  (if ((getattr (getattr os "path") "islink") path)
    (do (print (% "GATE\trefused\t%s\tsymlink" (tuple [name]))))
    (do
      (with [f (open path :encoding "utf-8")] (setv text ((getattr f "read"))))
      (setv [fails fm] (gate text))
      (setv target_dir (get DIRS (if fails "rejected" "ready")))
      (setv target_path ((getattr (getattr os "path") "join") target_dir name))
      (setv reason_path (+ target_path ".reason"))
      (setv collision (or ((getattr (getattr os "path") "lexists") target_path)
                          (and fails ((getattr (getattr os "path") "lexists") reason_path))))
      (if collision
        (do (print (% "GATE\trefused\t%s\toutput-exists" (tuple [name]))))
        (if fails
          (do
            (setv failed ((getattr (__import__ "operator") "iadd") failed 1))
            ((getattr shutil "move") path target_path)
            (with [f (open reason_path "w" :encoding "utf-8")] ((getattr f "write") (+ ((getattr "\n" "join") fails) "\n")))
            (print (% "GATE\tfail\t%s\t%s" (tuple [name ((getattr ";" "join") fails)])))
          )
          (do
            (setv passed ((getattr (__import__ "operator") "iadd") passed 1))
            ((getattr shutil "move") path target_path)
            (print (% "GATE\tpass\t%s\t%s" (tuple [name (cell_key fm)])))
          )
        )
      )
    )
  )
)
(defn cells_in [dirname]
  (setv seen {})
  (for [p ((getattr glob "glob") ((getattr (getattr os "path") "join") (get DIRS dirname) "*.md"))]
    (with [f (open p :encoding "utf-8")] (setv k (cell_key (front_matter ((getattr f "read"))))))
    (setv (get seen k) (+ ((getattr seen "get") k 0) 1))
  )
  (return seen)
)
(setv ready (cells_in "ready"))
(setv rejected (cells_in "rejected"))
(setv all_cells (lfor l (get curriculum "langs_rotation") t (get curriculum "themes") s (get t "stages") (tuple [t s l])))
(setv nxt None)
(for [[t s l] all_cells]
  (setv k (% "%s|%s|%s" (tuple [(get t "id") s l])))
  (if (and (not (in k ready)) (< ((getattr rejected "get") k 0) MAX_REJECTS_PER_CELL))
    (do
      (setv nxt (tuple [t s l]))
      (break)
    )
    None
  )
)
(m "drafts-gated" (+ passed failed))
(m "gate-pass" passed)
(m "gate-fail" failed)
(m "ready-total" (sum ((getattr ready "values"))))
(m "cells-ready" (% "%d/%d" (tuple [(len ready) (len all_cells)])))
(m "cells-stuck" (or ((getattr "," "join") (gfor [k v] ((getattr rejected "items")) :if (and (>= v MAX_REJECTS_PER_CELL) (not (in k ready))) k)) "none"))
(with [f (open LEDGER "a" :encoding "utf-8")] ((getattr f "write") (+ ((getattr json "dumps") {"ts" ((getattr time "strftime") "%Y-%m-%dT%H:%M:%S%z") "gate_pass" passed "gate_fail" failed "ready_total" (sum ((getattr ready "values"))) "cells_ready" (len ready) "cells_total" (len all_cells) "next" (if (not nxt) None (% "%s|%s|%s" (tuple [(get (get nxt 0) "id") (get nxt 1) (get nxt 2)])))} :ensure_ascii False) "\n")))
(if (not nxt)
  (do
    (print "BRIEF\tnone\tall cells have ready material or are stuck")
    ((getattr sys "exit") 0)
  )
  None
)
(setv [t s l] nxt)
(setv stage_ja (get (dfor x (get axes "stages") (get x "id") (get x "ja")) s))
(setv fname (% "%s__%s__%s__%s.md" (tuple [((getattr time "strftime") "%Y%m%d-%H%M") (get t "id") s l])))
(print (% "BRIEF\ttheme\t%s" (get t "id")))
(print (% "BRIEF\ttitle\t%s" (get t "title")))
(print (% "BRIEF\tgoal\t%s" (get t "goal")))
(print (% "BRIEF\tstage\t%s（%s）" (tuple [s stage_ja])))
(print (% "BRIEF\tlang\t%s" l))
(print (% "BRIEF\taxes\t%s" ((getattr "," "join") (get t "axes"))))
(print (% "BRIEF\toutput\t%s" ((getattr (getattr os "path") "join") (get DIRS "drafts") fname)))
(for [lid (get t "links")]
  (setv e ((getattr entries "get") lid))
  (if e
    (do (print (% "CITE\t%s\t%s\t%s\t%s" (tuple [(get e "name") ((getattr e "get") "url" "-") ((getattr e "get") "phone" "-") ((getattr e "get") "easy_ja" "")]))))
    None
  )
)
(for [x (get safety "emergency")]
  (if (in (get x "id") (tuple ["childline" "kodomo-sos" "yorisoi" "jidosodan-189"]))
    (do (print (% "SAFETY\t%s\t%s\t%s" (tuple [(get x "name") (get x "phone") ((getattr x "get") "url" "-")]))))
    None
  )
)
(setv prev ((getattr rejected "get") (% "%s|%s|%s" (tuple [(get t "id") s l])) 0))
(if prev
  (do
    (setv reasons [])
    (for [p ((getattr glob "glob") ((getattr (getattr os "path") "join") (get DIRS "rejected") (% "*__%s__%s__%s.md.reason" (tuple [(get t "id") s l]))))] (with [f (open p :encoding "utf-8")] ((getattr reasons "append") ((getattr ((getattr ((getattr f "read")) "strip")) "replace") "\n" ";"))))
    (print (% "BRIEF\tprevious-rejects\t%d\t%s" (tuple [prev ((getattr " | " "join") reasons)])))
  )
  None
)
