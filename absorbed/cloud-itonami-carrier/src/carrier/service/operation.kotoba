(ns carrier.service.operation)

;; Carrier Service Governor ⊣ Advisor — R0 skeleton.
;; All ops are :propose or :observe. Nothing here mutates a real person's line:
;; eSIM lifecycle stays in cloud-itonami-esim (its SIM-swap refusal is structural
;; and inherited), payment stays in nexus-x402, coverage truth stays external.

(def ops
  "The subscriber service plane. Each op declares its effect class; the
   governor treats anything not :observe as requiring a propose→govern round."
  [{:op/name :subscriber/signup    :op/effect :propose}
   {:op/name :subscriber/bill      :op/effect :propose}
   {:op/name :subscriber/support   :op/effect :propose}
   {:op/name :network/observe      :op/effect :observe}
   {:op/name :outage/notify        :op/effect :propose}])

(def op-names
  (set (map :op/name ops)))

(defn observable?
  "Only :network/observe is a pure observation. Everything else must round-trip
   through the governor."
  [op-name]
  (= op-name :network/observe))

(defn admitted-op?
  [op-name]
  (contains? op-names op-name))

(defn propose
  "Advisor side: build a proposal. R0 returns the proposal verbatim; the
   governor reviews it. Never executes directly."
  [op-name payload]
  (when-not (admitted-op? op-name)
    (throw (ex-info "op not admitted" {:op/name op-name :admitted op-names})))
  {:proposal/op     op-name
   :proposal/effect (get (into {} (map (juxt :op/name :op/effect) ops)) op-name)
   :proposal/payload payload
   :proposal/status  :pending-govern})

(defn govern
  "Governor side: review a proposal. R0 policy: everything passes through
   recorded (audit trail) — but :propose ops are never auto-executed, they
   return :approved-for-review for a human/owner layer. The esim actor's
   structural refusal (ownership/transfer absent from :auto forever) is
   inherited here: even if someone asks, there is no code path that executes it."
  [{:proposal/keys [op effect] :as proposal}]
  (when-not (admitted-op? op)
    (throw (ex-info "op not admitted" {:op/name op :admitted op-names})))
  (if (= effect :observe)
    (assoc proposal :proposal/status :done)
    (assoc proposal :proposal/status :approved-for-review
                    :proposal/note "R0: propose-only; execution path does not exist yet")))
