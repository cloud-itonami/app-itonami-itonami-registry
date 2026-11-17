(ns carrier.service.operation-test
  (:require [clojure.test :refer [deftest is testing]]
            [carrier.service.operation :as op]))

(deftest ops-are-declared-with-effect-classes
  (testing "five subscriber-plane ops, none of them mutate a line"
    (is (= #{:subscriber/signup :subscriber/bill :subscriber/support
             :network/observe :outage/notify}
           op/op-names))
    (is (op/observable? :network/observe))
    (is (not (op/observable? :subscriber/signup)))))

(deftest unknown-ops-are-refused
  (testing "no ambient ops: an unadmitted op name throws"
    (is (thrown? clojure.lang.ExceptionInfo (op/propose :ownership/transfer {})))
    (is (thrown? clojure.lang.ExceptionInfo (op/govern {:proposal/op :ownership/transfer})))))

(deftest propose-never-executes
  (testing "proposal comes back pending-govern, not done"
    (let [p (op/propose :subscriber/signup {:draft true})]
      (is (= :pending-govern (:proposal/status p)))
      (is (= :propose (:proposal/effect p))))))

(deftest propose-ops-never-auto-execute
  (testing "R0 policy: :propose ops return approved-for-review (execution path does not exist)"
    (is (= :approved-for-review (:proposal/status (op/govern (op/propose :subscriber/bill {})))))))

(deftest observe-ops-complete
  (testing ":network/observe is a pure observation and completes in-govern"
    (let [p (op/propose :network/observe {:ts "2026-09-01T00:00:00Z"})]
      (is (= :done (:proposal/status (op/govern p)))))))

(deftest sim-swap-refusal-is-structural
  (testing "ownership/transfer is not an op here at all — the esim actor's
            permanent structural refusal is inherited, not reimplemented"
    (is (not (contains? op/op-names :ownership/transfer)))
    (is (not (contains? op/op-names :profile/download)))
    (is (not (contains? op/op-names :profile/lifecycle)))))
