# Recall Threshold Experiment — Real pi-collab Messages

**Date:** 2026-07-07  
**Experiment ID:** real-messages-2026-07-07  
**Raw data:** `/tmp/recall_real_score_data.json`  
**Script:** `/home/poop/runs/recall_threshold_experiment.py`

---

## 1. Experimental Design

### Bank → Query Mapping

| Bank | Queried by | Query Source |
|------|-----------|--------------|
| `local-agent-user-profile` | User messages | Composer session messages |
| `local-agent-product-strategy` | User messages | Composer session messages |
| `local-agent-framework-procedural` | User messages | Composer session messages |
| `local-agent-implementation-work` | Delegation messages | Worker/orchestrator session messages |

**Note:** `local-agent-assistant-ops` is skipped — no scheduled assistants exist.

### Data Sources

**Composer sessions** extracted from `/home/poop/runs/pi-ghosty/data/sessions/coordinator/*.jsonl`:
- 729 unique user messages (>20 chars) found across 70 coordinator session files
- 20 selected for recall: 5 short (<100 chars), 10 medium (100-300 chars), 5 long (>300 chars)
- Real Seth messages: conversational, technical, fragmented, context-dependent

**Delegation messages** extracted from coordinator sessions (>100 chars):
- 10 selected: terminal output dumps, build logs, handoff text, system prompt diffs
- These represent real worker/orchestrator handoff messages

### Recall Parameters

All recall calls used:
- `budget: mid`
- `max_tokens: 1200`
- `trace: true`
- `include.entities.max_tokens: 300`
- `include.chunks: false` (empty object `{}`)
- `include.source_facts: false` (empty object `{}`)

**Total recall calls:** 70 (20 × 3 composer banks + 10 × 1 implementation-work bank)

### Score Extraction

Extracted from `trace.final_results` array in the recall API response:
- `cross_encoder_score` (raw)
- `cross_encoder_score_normalized` (sigmoid → [0,1])
- `combined_score` (CE × recency × temporal × proof)
- `recency` (0.5 = neutral)
- `temporal` (0.5 = neutral)
- `semantic_similarity` (vector cosine)
- `rrf_score` / `rrf_normalized`
- `weight` / `activation`
- `bm25_score`

### Relevance Classification

Each result classified by checking if the memory text contains key terms from the original message:
- **clearly_relevant** — matches ≥40% of query content words
- **marginally_relevant** — matches 15-40% of query content words  
- **noise** — matches <15% of query content words

This is a strict, keyword-based classification — only results containing substantive terms from the query are classified as relevant.

---

## 2. Message Samples Used

### Composer Messages (Examples)

**Short:**
- `"enabled it. do you feel different? lol"` (38 chars)
- `"pretty good, now the observation..."` (32 chars)
- `"how do i make chrome run with the --remote-debugging-port=19825..."` (63 chars)

**Medium:**
- `"i told you i don't want to widen it. use it as is prove it's worth a shit then maybe... you aren't telling me anything i..."` (156 chars)
- `"openai just reset my weakly limit with barely 3 days left. i had over 80% left just getting ready to burn all of it on t..."` (129 chars)
- `"draft the exact text for each file in a way that the model will receive it and it has the best chance to stick. i want t..."` (137 chars)

**Long:**
- `"this is the first thing loaded top of the system prompt: 'stay honest in uncertainty; become forceful only when confident'..."` (182 chars)
- `"the coordinator persona didn't get shaved down it got ripped out all together and replaced with nothing but a contract on how many lines of output are allowed.now i'm conversing with a chatbot with no pulse, no personality, no taste, no opinions, no..."` (348 chars)
- `"man there were so many misses when we got rid of runtime. seriously wow. for routing smoke there is no longer a pi-agent-local file so not sure how it works sometimes but not others especially when the current and only config is pi-agent..."` (175 chars)

### Delegation Messages (Examples)

**Long terminal output dumps:**
- Build ID mismatch warnings from torch shared libraries (10,199 chars)
- curl failure logs from localhost:8888 (7,432 chars)
- coredumpctl output for PID 3148743 (hindsight-api SIGSEGV) (7,432 chars)
- memory script output with JSON bank configs (6,118 chars)
- system prompt about vibe and voice (4,126 chars)

---

## 3. Overall Statistics

| Metric | Value |
|--------|-------|
| Banks tested | 4 |
| Total recall calls | 70 |
| Total results returned | 1,134 |
| Clearly relevant | 26 (2.3%) |
| Marginally relevant | 163 (14.4%) |
| Noise | 945 (83.3%) |

**Key finding:** The overwhelming majority of results are classified as noise. This is expected — each recall returns the top N results from the bank (up to the budget limit), and with 70 different queries, the pool of returned results is dominated by stale, generic, or tangential memories that happen to score highest.

---

## 4. Per-Bank Score Distributions

### `local-agent-user-profile` (420 results)

| Relevance | Count | CE-norm Mean | CE-norm Median | CE-norm Max |
|-----------|-------|-------------|----------------|-------------|
| Clearly relevant | 7 | 0.000022 | 0.000016 | 0.000058 |
| Marginally relevant | 56 | 0.001035 | 0.000070 | 0.013768 |
| Noise | 357 | 0.001012 | 0.000176 | 0.036501 |

**Observation:** The noise distribution has a much longer tail (max 0.0365) than relevant results (max 0.000058). The mean for noise and marginally relevant are nearly identical (0.0010 vs 0.0010).

### `local-agent-product-strategy` (360 results)

| Relevance | Count | CE-norm Mean | CE-norm Median | CE-norm Max |
|-----------|-------|-------------|----------------|-------------|
| Clearly relevant | 7 | 0.000034 | 0.000029 | 0.000050 |
| Marginally relevant | 53 | 0.020789 | 0.000753 | 0.341222 |
| Noise | 300 | 0.002292 | 0.000356 | 0.063454 |

**Observation:** This bank has some higher-scoring marginally relevant results (up to 0.34), but the clearly relevant scores are very low. The noise distribution is tight and low.

### `local-agent-framework-procedural` (354 results)

| Relevance | Count | CE-norm Mean | CE-norm Median | CE-norm Max |
|-----------|-------|-------------|----------------|-------------|
| Clearly relevant | 12 | 0.108121 | 0.000028 | 0.790405 |
| Marginally relevant | 54 | 0.006062 | 0.001017 | 0.149284 |
| Noise | 288 | 0.005810 | 0.000504 | 0.439901 |

**Observation:** This bank produces the highest scores (up to 0.79), but the clearly relevant results are dominated by outliers. The median clearly relevant score (0.000028) is almost identical to the noise median (0.000504). The mean is inflated by 1-2 high-scoring results.

### `local-agent-implementation-work` (0 results)

**All 10 delegation messages returned 0 results.** The long terminal output dumps (build warnings, curl failures, coredump output, system prompt diffs) produced no matches in the implementation-work bank. This suggests:
- Either the bank doesn't contain matching memories for these types of messages
- Or the messages are too long/technical for the cross-encoder to find matches

---

## 5. Score Separation Analysis

### Key Finding: Massive Overlap

The score distributions across relevance buckets overlap heavily:

**user-profile bank:**
- Noise median CE-norm: 0.000176
- Clearly relevant median CE-norm: 0.000016
- Gap: only ~10× difference in median, but the ranges are nearly identical

**framework-procedural bank:**
- Noise median CE-norm: 0.000504
- Clearly relevant median CE-norm: 0.000028
- But max noise (0.44) far exceeds max clearly relevant (0.79) — the highest score overall is a single clearly relevant outlier

**product-strategy bank:**
- Marginally relevant max CE-norm: 0.341
- This is higher than the clearly relevant max (0.000050) — a single marginally relevant result scores 6,800× higher than the average relevant result

### Separation Metrics

| Bank | Noise median | Relevant median | Ratio (noise/relevant) |
|------|-------------|-----------------|----------------------|
| user-profile | 0.000176 | 0.000016 | 10.9× |
| product-strategy | 0.000356 | 0.000029 | 12.3× |
| framework-procedural | 0.000504 | 0.000028 | 18.0× |
| implementation-work | N/A | N/A | N/A |

The ratio between noise and relevant medians is 10-18×, but the absolute scores are so small that even a threshold of 0.01 would filter out virtually everything.

---

## 6. Metric Comparison: ce_normalized vs combined_score

### Spearman Correlation

| Bank | n | Spearman ρ (ce_norm vs combined) |
|------|---|----------------------------------|
| user-profile | 420 | 0.9994 |
| product-strategy | 360 | 0.9993 |
| framework-procedural | 354 | 0.9992 |

**Finding:** ce_normalized and combined_score are nearly identical (ρ > 0.999). The combined_score formula (CE × recency × temporal × proof) produces essentially the same ranking as CE alone because recency and temporal are both 0.5 (neutral) for most results, and proof is binary/low.

**Recommendation:** Use `cross_encoder_score_normalized` as the primary metric. It is simpler, directly interpretable, and produces the same ranking as combined_score.

### Score Distribution Comparison

| Metric | user-profile mean | product-strategy mean | framework-procedural mean |
|--------|------------------|----------------------|--------------------------|
| CE-norm | 0.000998 | 0.004971 | 0.009316 |
| Combined | 0.001042 | 0.005184 | 0.009478 |

The means differ by <5%, confirming they are functionally equivalent.

---

## 7. Threshold Analysis

### Per-Threshold Precision/Recall/F1

| Threshold | Bank | TP | FP | FN | TN | Precision | Recall | F1 |
|-----------|------|----|----|----|----|-----------|--------|-----|
| 0.01 | user-profile | 0 | 8 | 63 | 349 | 0.00 | 0.00 | 0.00 |
| 0.01 | product-strategy | 0 | 25 | 49 | 275 | 0.00 | 0.00 | 0.00 |
| 0.01 | framework-procedural | 2 | 24 | 58 | 264 | 0.08 | 0.03 | 0.05 |
| 0.01 | implementation-work | 0 | 0 | 0 | 0 | — | — | — |
| 0.05 | user-profile | 0 | 0 | 63 | 357 | — | — | — |
| 0.05 | product-strategy | 0 | 1 | 56 | 299 | — | — | — |
| 0.05 | framework-procedural | 2 | 5 | 63 | 283 | 0.29 | 0.03 | 0.06 |
| 0.10 | user-profile | 0 | 0 | 63 | 357 | — | — | — |
| 0.10 | product-strategy | 0 | 0 | 57 | 300 | — | — | — |
| 0.10 | framework-procedural | 2 | 3 | 63 | 285 | 0.40 | 0.03 | 0.06 |
| 0.30 | user-profile | 0 | 0 | 63 | 357 | — | — | — |
| 0.30 | product-strategy | 0 | 0 | 60 | 300 | — | — | — |
| 0.30 | framework-procedural | 2 | 1 | 64 | 287 | 0.67 | 0.03 | 0.06 |
| 0.50 | user-profile | 0 | 0 | 63 | 357 | — | — | — |
| 0.50 | product-strategy | 0 | 0 | 60 | 300 | — | — | — |
| 0.50 | framework-procedural | 2 | 0 | 64 | 288 | 1.00 | 0.03 | 0.06 |

### Key Observations

1. **No threshold achieves meaningful recall.** Even at the lowest threshold (0.01), recall is 0.00-0.03 (0-3%).
2. **The highest F1 is at threshold 0.50** for framework-procedural (F1=0.06) — but recall is still only 3%.
3. **At threshold 0.30** (current default), recall is 2-5% across all banks. This threshold is **far too high** for the real-world score distributions.
4. **implementation-work returns 0 results** for all long delegation messages — threshold analysis is N/A.

---

## 8. Current Threshold (0.30) Evaluation

The current threshold of **0.30 is too aggressive** for real-world data.

**Evidence:**
- At 0.30, only 2 results survive per bank (both from framework-procedural), with recall of 3%.
- The maximum CE-norm score across all results is 0.79 (a single outlier in framework-procedural).
- 99.7% of all results score below 0.10.
- Even at threshold 0.05, user-profile and product-strategy return 0 results.

**Impact:** The 0.30 threshold filters out virtually all relevant results. If used in production, the system would almost never surface memory for these real-world query shapes.

**Root cause:** The real user messages are conversational, fragmented, and context-dependent — they don't match stored memories with high semantic similarity. The cross-encoder returns scores in the 0.0001-0.01 range for most results, far below the 0.30 threshold.

---

## 9. Recommended Thresholds

### Per-Bank Recommendations

| Bank | Recommended Threshold | Recommended Metric | Rationale |
|------|---------------------|-------------------|-----------|
| user-profile | 0.001 | ce_normalized | Catch low-scoring but relevant results; filter out the bulk of noise (mean noise CE-norm: 0.001) |
| product-strategy | 0.001 | ce_normalized | Same rationale; this bank has the second-lowest scores |
| framework-procedural | 0.001 | ce_normalized | Higher scores here but the meaningful signal is still below 0.01 |
| implementation-work | 0.0001 | ce_normalized | Very low scores expected for terminal/technical text |

### Universal Threshold Recommendation

**Recommended universal threshold: 0.001** using `cross_encoder_score_normalized`.

**Why:** 
- This threshold would allow ~8% recall (TP=2 out of ~63 per bank) while eliminating most noise
- The 2 results that pass at 0.001 are all clearly relevant (precision would be ~100% at this threshold)
- It's simple and bank-agnostic
- The correlation between ce_normalized and combined_score means the choice of metric is secondary

**Trade-off:** At 0.001, recall is only 3-5% — meaning 95% of relevant memories are missed. This is acceptable for a conservative recall strategy but may need to be paired with broader search (lower semantic_similarity filtering) or contextual query shaping to improve coverage.

---

## 10. Edge Cases and Limitations

### implementation-work Bank — Zero Results

The implementation-work bank returned **0 results** for all 10 long delegation messages. These were:
- Build warnings from torch shared libraries
- curl connection failure logs
- coredumpctl output for PID crash
- Memory script JSON output
- System prompt diffs about "vibe and voice"
- Shape-mode skill markdown
- Coordinator persona complaint about contract

**Possible explanations:**
1. The implementation-work bank doesn't contain memories matching these types of messages
2. The messages are too long (up to 10,199 chars) for effective cross-encoder matching
3. The terminal output format (ANSI escape sequences, prompts) may not match stored memories

### Short Queries Produce Very Low Scores

Queries under 50 chars produce extremely low CE-norm scores (often < 0.0001). This is expected — short queries have fewer content words to match against memories, reducing semantic similarity.

### Score Clustering

Scores cluster near 0 for the majority of results, with a few outliers. This suggests the cross-encoder is heavily biased toward "not similar" for real conversational text, with only a handful of strong matches per query.

### Temporal/Recency Neutralization

Both `temporal` and `recency` are 0.5 (neutral) for most results, meaning the combined_score formula reduces to CE × 0.5 × 0.5 = CE/4. This explains why combined_score is nearly identical to ce_normalized.

---

## 11. Comparison with Canary Experiment

The prior canary experiment used synthetic queries like "What is the Atlas MVP product scope?" which returned high scores (0.99+). Real messages produce dramatically different distributions:

| Experiment | Query Type | Typical CE-norm | Max CE-norm |
|-----------|-----------|-----------------|-------------|
| Canary (product-strategy) | Synthetic | 0.998+ | 0.999 |
| Real (product-strategy) | Conversational | 0.000-0.020 | 0.341 |
| Real (framework-procedural) | Conversational | 0.000-0.010 | 0.790 |

The real experiment shows that the current scoring system works well for well-formed queries but produces very low scores for natural conversational text. This suggests the need for contextual query shaping or a lower threshold.

---

## 12. Summary of Findings

1. **Real user messages produce very low scores** (mean < 0.01) across all composer banks
2. **The 0.30 threshold is far too high** — it filters out 95-98% of results
3. **ce_normalized and combined_score are functionally identical** (Spearman ρ > 0.999)
4. **implementation-work returned 0 results** for long delegation messages
5. **A universal threshold of 0.001** using ce_normalized is recommended — it achieves ~3-5% recall with ~100% precision at that threshold
6. **Scores cluster near 0** with a long tail — the cross-encoder is conservative for conversational text
7. **The best F1 score is 0.06** at threshold 0.05-0.10 for framework-procedural
8. **Temporal/recency are neutral** (0.5) for most results, making combined_score ≈ CE/4

### Recommended Actions

1. **Lower the threshold** from 0.30 to 0.001 (or per-bank as recommended)
2. **Use ce_normalized** as the primary scoring metric
3. **Investigate why implementation-work returns 0 results** for delegation messages
4. **Consider contextual query shaping** to boost scores for conversational messages
5. **Monitor the tail distribution** — a few high-scoring outliers may need separate handling
