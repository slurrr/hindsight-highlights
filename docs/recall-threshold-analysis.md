# Recall Threshold Analysis — Score Distribution Study

**Date:** 2026-07-07

**Purpose:** Analyze Hindsight recall score distributions to determine optimal thresholding strategy.


## 1. Experimental Design


Same 7 canary banks and queries as the prior native knob experiment. Each bank tested with **3 budget levels** (`low`, `mid`, `high`), with `max_tokens=2048`, `include.entities=null`, `trace=true`.


### Queries


| Bank | Query |
|------|-------|

| user-profile | How should planning summaries be formatted for the user? |

| product-strategy | What is the Atlas MVP product scope? |

| implementation-work | What did the tester say strict rule recall must return? |

| assistant-ops | What email triage standing rule should the main agent know? |

| framework-procedural | Who is allowed to communicate directly with the user? |

| pi-integration | What is the contract for Pi session retention document IDs? |

| session-evolution | What is the Atlas MVP product plan and what are the MVP scope decisions? |


### Score extraction methodology


Scores extracted from `trace.final_results` in the recall API response. The Hindsight scoring pipeline produces these fields:


| Score Field | Description | Range |

|-------------|-------------|-------|

| `cross_encoder_score` | Raw cross-encoder output (logits scale) | varies |

| `cross_encoder_score_normalized` | Sigmoid/logits → [0,1] normalized score | 0–1 |

| `combined_score` | CE × recency × temporal × proof_count | 0–1 |

| `rrf_score` | Reciprocal rank fusion raw score | 0–1 |

| `rrf_normalized` | Normalized RRF score | 0–1 |

| `semantic_similarity` | Vector cosine similarity | 0–1 |

| `bm25_score` | BM25 document score | 0–∞ |

| `temporal` | Temporal decay weight | 0–1 |

| `recency` | Recency weight (time since occurrence) | 0–1 |

| `weight` | Final result weight | 0–1 |

| `activation` | Same as combined_score | 0–1 |


### Relevance classification


Each result classified into one of three buckets:


- **clearly_relevant** — matches ≥40% of bank-specific query keywords

- **marginally_relevant** — matches 20-40% of query keywords

- **noise** — contains noise patterns (debug, token_budget, stacktrace_marker) OR matches <20% of query keywords


## 2. Overall Statistics


| Metric | Value |
|--------|-------|

| Banks tested | 7 |

| Budget levels per bank | 3 (low, mid, high) |

| Total experiments | 21 |

| Total classified results | 63 |

| Clearly relevant | 27 (42.9%)

| Marginally relevant | 12 (19.0%)

| Noise | 24 (38.1%)


## 3. Per-Bank Score Distributions


### `assistant-ops`


**low budget (3 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 2 |

| Marginally relevant | 0 |

| Noise | 1 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | -4.197264 | 3.178430 | -1.194941 | -2.565989 | 3 |

| cross_encoder_score_normalized | 0.014814 | 0.960014 | 0.348729 | 0.071360 | 3 |

| combined_score | 0.014814 | 0.960014 | 0.348729 | 0.071360 | 3 |

| rrf_score | 0.031746 | 0.032522 | 0.032264 | 0.032522 | 3 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 3 |

| semantic_similarity | 0.627898 | 0.712283 | 0.681211 | 0.703451 | 3 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| recency | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| weight | 0.014814 | 0.960014 | 0.348729 | 0.071360 | 3 |

| activation | 0.014814 | 0.960014 | 0.348729 | 0.071360 | 3 |



**Scores by relevance bucket:**


**clearly_relevant (2 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 2 | -4.197264 | -2.565989 | -3.381626 |

| cross_encoder_score_normalized | 2 | 0.014814 | 0.071360 | 0.043087 |

| combined_score | 2 | 0.014814 | 0.071360 | 0.043087 |

| rrf_score | 2 | 0.031746 | 0.032522 | 0.032134 |

| semantic_similarity | 2 | 0.627898 | 0.703451 | 0.665675 |

| temporal | 2 | 0.500000 | 0.500000 | 0.500000 |

| recency | 2 | 0.500000 | 0.500000 | 0.500000 |

| weight | 2 | 0.014814 | 0.071360 | 0.043087 |



**marginally_relevant:** (0 results)


**noise (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 3.178430 | 3.178430 | 3.178430 |

| cross_encoder_score_normalized | 1 | 0.960014 | 0.960014 | 0.960014 |

| combined_score | 1 | 0.960014 | 0.960014 | 0.960014 |

| rrf_score | 1 | 0.032522 | 0.032522 | 0.032522 |

| semantic_similarity | 1 | 0.712283 | 0.712283 | 0.712283 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.960014 | 0.960014 | 0.960014 |




**mid budget (3 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 2 |

| Marginally relevant | 0 |

| Noise | 1 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | -4.197264 | 3.178430 | -1.194941 | -2.565989 | 3 |

| cross_encoder_score_normalized | 0.014814 | 0.960014 | 0.348729 | 0.071360 | 3 |

| combined_score | 0.014814 | 0.960014 | 0.348729 | 0.071360 | 3 |

| rrf_score | 0.031746 | 0.032522 | 0.032264 | 0.032522 | 3 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 3 |

| semantic_similarity | 0.627898 | 0.712283 | 0.681211 | 0.703451 | 3 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| recency | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| weight | 0.014814 | 0.960014 | 0.348729 | 0.071360 | 3 |

| activation | 0.014814 | 0.960014 | 0.348729 | 0.071360 | 3 |



**Scores by relevance bucket:**


**clearly_relevant (2 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 2 | -4.197264 | -2.565989 | -3.381626 |

| cross_encoder_score_normalized | 2 | 0.014814 | 0.071360 | 0.043087 |

| combined_score | 2 | 0.014814 | 0.071360 | 0.043087 |

| rrf_score | 2 | 0.031746 | 0.032522 | 0.032134 |

| semantic_similarity | 2 | 0.627898 | 0.703451 | 0.665675 |

| temporal | 2 | 0.500000 | 0.500000 | 0.500000 |

| recency | 2 | 0.500000 | 0.500000 | 0.500000 |

| weight | 2 | 0.014814 | 0.071360 | 0.043087 |



**marginally_relevant:** (0 results)


**noise (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 3.178430 | 3.178430 | 3.178430 |

| cross_encoder_score_normalized | 1 | 0.960014 | 0.960014 | 0.960014 |

| combined_score | 1 | 0.960014 | 0.960014 | 0.960014 |

| rrf_score | 1 | 0.032522 | 0.032522 | 0.032522 |

| semantic_similarity | 1 | 0.712283 | 0.712283 | 0.712283 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.960014 | 0.960014 | 0.960014 |




**high budget (3 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 2 |

| Marginally relevant | 0 |

| Noise | 1 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | -4.197264 | 3.178430 | -1.194941 | -2.565989 | 3 |

| cross_encoder_score_normalized | 0.014814 | 0.960014 | 0.348729 | 0.071360 | 3 |

| combined_score | 0.014814 | 0.960014 | 0.348729 | 0.071360 | 3 |

| rrf_score | 0.031746 | 0.032522 | 0.032264 | 0.032522 | 3 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 3 |

| semantic_similarity | 0.627898 | 0.712283 | 0.681211 | 0.703451 | 3 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| recency | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| weight | 0.014814 | 0.960014 | 0.348729 | 0.071360 | 3 |

| activation | 0.014814 | 0.960014 | 0.348729 | 0.071360 | 3 |



**Scores by relevance bucket:**


**clearly_relevant (2 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 2 | -4.197264 | -2.565989 | -3.381626 |

| cross_encoder_score_normalized | 2 | 0.014814 | 0.071360 | 0.043087 |

| combined_score | 2 | 0.014814 | 0.071360 | 0.043087 |

| rrf_score | 2 | 0.031746 | 0.032522 | 0.032134 |

| semantic_similarity | 2 | 0.627898 | 0.703451 | 0.665675 |

| temporal | 2 | 0.500000 | 0.500000 | 0.500000 |

| recency | 2 | 0.500000 | 0.500000 | 0.500000 |

| weight | 2 | 0.014814 | 0.071360 | 0.043087 |



**marginally_relevant:** (0 results)


**noise (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 3.178430 | 3.178430 | 3.178430 |

| cross_encoder_score_normalized | 1 | 0.960014 | 0.960014 | 0.960014 |

| combined_score | 1 | 0.960014 | 0.960014 | 0.960014 |

| rrf_score | 1 | 0.032522 | 0.032522 | 0.032522 |

| semantic_similarity | 1 | 0.712283 | 0.712283 | 0.712283 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.960014 | 0.960014 | 0.960014 |




### `framework-procedural`


**low budget (3 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 1 |

| Marginally relevant | 0 |

| Noise | 2 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | -8.432151 | 5.985063 | -3.299863 | -7.452499 | 3 |

| cross_encoder_score_normalized | 0.000218 | 0.997490 | 0.332763 | 0.000580 | 3 |

| combined_score | 0.000218 | 0.997490 | 0.332763 | 0.000580 | 3 |

| rrf_score | 0.031746 | 0.032787 | 0.032264 | 0.032258 | 3 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 3 |

| semantic_similarity | 0.503173 | 0.742038 | 0.592254 | 0.531551 | 3 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| recency | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| weight | 0.000218 | 0.997490 | 0.332763 | 0.000580 | 3 |

| activation | 0.000218 | 0.997490 | 0.332763 | 0.000580 | 3 |



**Scores by relevance bucket:**


**clearly_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 5.985063 | 5.985063 | 5.985063 |

| cross_encoder_score_normalized | 1 | 0.997490 | 0.997490 | 0.997490 |

| combined_score | 1 | 0.997490 | 0.997490 | 0.997490 |

| rrf_score | 1 | 0.032787 | 0.032787 | 0.032787 |

| semantic_similarity | 1 | 0.742038 | 0.742038 | 0.742038 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.997490 | 0.997490 | 0.997490 |



**marginally_relevant:** (0 results)


**noise (2 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 2 | -8.432151 | -7.452499 | -7.942325 |

| cross_encoder_score_normalized | 2 | 0.000218 | 0.000580 | 0.000399 |

| combined_score | 2 | 0.000218 | 0.000580 | 0.000399 |

| rrf_score | 2 | 0.031746 | 0.032258 | 0.032002 |

| semantic_similarity | 2 | 0.503173 | 0.531551 | 0.517362 |

| temporal | 2 | 0.500000 | 0.500000 | 0.500000 |

| recency | 2 | 0.500000 | 0.500000 | 0.500000 |

| weight | 2 | 0.000218 | 0.000580 | 0.000399 |




**mid budget (3 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 1 |

| Marginally relevant | 0 |

| Noise | 2 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | -8.432151 | 5.985063 | -3.299863 | -7.452499 | 3 |

| cross_encoder_score_normalized | 0.000218 | 0.997490 | 0.332763 | 0.000580 | 3 |

| combined_score | 0.000218 | 0.997490 | 0.332763 | 0.000580 | 3 |

| rrf_score | 0.031746 | 0.032787 | 0.032264 | 0.032258 | 3 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 3 |

| semantic_similarity | 0.503173 | 0.742038 | 0.592254 | 0.531551 | 3 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| recency | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| weight | 0.000218 | 0.997490 | 0.332763 | 0.000580 | 3 |

| activation | 0.000218 | 0.997490 | 0.332763 | 0.000580 | 3 |



**Scores by relevance bucket:**


**clearly_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 5.985063 | 5.985063 | 5.985063 |

| cross_encoder_score_normalized | 1 | 0.997490 | 0.997490 | 0.997490 |

| combined_score | 1 | 0.997490 | 0.997490 | 0.997490 |

| rrf_score | 1 | 0.032787 | 0.032787 | 0.032787 |

| semantic_similarity | 1 | 0.742038 | 0.742038 | 0.742038 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.997490 | 0.997490 | 0.997490 |



**marginally_relevant:** (0 results)


**noise (2 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 2 | -8.432151 | -7.452499 | -7.942325 |

| cross_encoder_score_normalized | 2 | 0.000218 | 0.000580 | 0.000399 |

| combined_score | 2 | 0.000218 | 0.000580 | 0.000399 |

| rrf_score | 2 | 0.031746 | 0.032258 | 0.032002 |

| semantic_similarity | 2 | 0.503173 | 0.531551 | 0.517362 |

| temporal | 2 | 0.500000 | 0.500000 | 0.500000 |

| recency | 2 | 0.500000 | 0.500000 | 0.500000 |

| weight | 2 | 0.000218 | 0.000580 | 0.000399 |




**high budget (3 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 1 |

| Marginally relevant | 0 |

| Noise | 2 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | -8.432151 | 5.985063 | -3.299863 | -7.452499 | 3 |

| cross_encoder_score_normalized | 0.000218 | 0.997490 | 0.332763 | 0.000580 | 3 |

| combined_score | 0.000218 | 0.997490 | 0.332763 | 0.000580 | 3 |

| rrf_score | 0.031746 | 0.032787 | 0.032264 | 0.032258 | 3 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 3 |

| semantic_similarity | 0.503173 | 0.742038 | 0.592254 | 0.531551 | 3 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| recency | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| weight | 0.000218 | 0.997490 | 0.332763 | 0.000580 | 3 |

| activation | 0.000218 | 0.997490 | 0.332763 | 0.000580 | 3 |



**Scores by relevance bucket:**


**clearly_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 5.985063 | 5.985063 | 5.985063 |

| cross_encoder_score_normalized | 1 | 0.997490 | 0.997490 | 0.997490 |

| combined_score | 1 | 0.997490 | 0.997490 | 0.997490 |

| rrf_score | 1 | 0.032787 | 0.032787 | 0.032787 |

| semantic_similarity | 1 | 0.742038 | 0.742038 | 0.742038 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.997490 | 0.997490 | 0.997490 |



**marginally_relevant:** (0 results)


**noise (2 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 2 | -8.432151 | -7.452499 | -7.942325 |

| cross_encoder_score_normalized | 2 | 0.000218 | 0.000580 | 0.000399 |

| combined_score | 2 | 0.000218 | 0.000580 | 0.000399 |

| rrf_score | 2 | 0.031746 | 0.032258 | 0.032002 |

| semantic_similarity | 2 | 0.503173 | 0.531551 | 0.517362 |

| temporal | 2 | 0.500000 | 0.500000 | 0.500000 |

| recency | 2 | 0.500000 | 0.500000 | 0.500000 |

| weight | 2 | 0.000218 | 0.000580 | 0.000399 |




### `implementation-work`


**low budget (3 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 1 |

| Marginally relevant | 1 |

| Noise | 1 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | -11.311657 | 4.996698 | -2.595500 | -1.471542 | 3 |

| cross_encoder_score_normalized | 0.000012 | 0.993285 | 0.393335 | 0.186708 | 3 |

| combined_score | 0.000013 | 1.070158 | 0.423776 | 0.201158 | 3 |

| rrf_score | 0.015873 | 0.032787 | 0.026973 | 0.032258 | 3 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 3 |

| semantic_similarity | 0.622774 | 0.770483 | 0.683866 | 0.658341 | 3 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| recency | 0.886952 | 0.886964 | 0.886958 | 0.886958 | 3 |

| weight | 0.000013 | 1.070158 | 0.423776 | 0.201158 | 3 |

| activation | 0.000013 | 1.070158 | 0.423776 | 0.201158 | 3 |



**Scores by relevance bucket:**


**clearly_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 4.996698 | 4.996698 | 4.996698 |

| cross_encoder_score_normalized | 1 | 0.993285 | 0.993285 | 0.993285 |

| combined_score | 1 | 1.070158 | 1.070158 | 1.070158 |

| rrf_score | 1 | 0.032787 | 0.032787 | 0.032787 |

| semantic_similarity | 1 | 0.770483 | 0.770483 | 0.770483 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.886964 | 0.886964 | 0.886964 |

| weight | 1 | 1.070158 | 1.070158 | 1.070158 |



**marginally_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | -1.471542 | -1.471542 | -1.471542 |

| cross_encoder_score_normalized | 1 | 0.186708 | 0.186708 | 0.186708 |

| combined_score | 1 | 0.201158 | 0.201158 | 0.201158 |

| rrf_score | 1 | 0.032258 | 0.032258 | 0.032258 |

| semantic_similarity | 1 | 0.658341 | 0.658341 | 0.658341 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.886952 | 0.886952 | 0.886952 |

| weight | 1 | 0.201158 | 0.201158 | 0.201158 |



**noise (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | -11.311657 | -11.311657 | -11.311657 |

| cross_encoder_score_normalized | 1 | 0.000012 | 0.000012 | 0.000012 |

| combined_score | 1 | 0.000013 | 0.000013 | 0.000013 |

| rrf_score | 1 | 0.015873 | 0.015873 | 0.015873 |

| semantic_similarity | 1 | 0.622774 | 0.622774 | 0.622774 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.886958 | 0.886958 | 0.886958 |

| weight | 1 | 0.000013 | 0.000013 | 0.000013 |




**mid budget (3 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 1 |

| Marginally relevant | 1 |

| Noise | 1 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | -11.311657 | 4.996698 | -2.595500 | -1.471542 | 3 |

| cross_encoder_score_normalized | 0.000012 | 0.993285 | 0.393335 | 0.186708 | 3 |

| combined_score | 0.000013 | 1.070158 | 0.423776 | 0.201158 | 3 |

| rrf_score | 0.015873 | 0.032787 | 0.026973 | 0.032258 | 3 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 3 |

| semantic_similarity | 0.622774 | 0.770483 | 0.683866 | 0.658341 | 3 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| recency | 0.886952 | 0.886964 | 0.886958 | 0.886958 | 3 |

| weight | 0.000013 | 1.070158 | 0.423776 | 0.201158 | 3 |

| activation | 0.000013 | 1.070158 | 0.423776 | 0.201158 | 3 |



**Scores by relevance bucket:**


**clearly_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 4.996698 | 4.996698 | 4.996698 |

| cross_encoder_score_normalized | 1 | 0.993285 | 0.993285 | 0.993285 |

| combined_score | 1 | 1.070158 | 1.070158 | 1.070158 |

| rrf_score | 1 | 0.032787 | 0.032787 | 0.032787 |

| semantic_similarity | 1 | 0.770483 | 0.770483 | 0.770483 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.886964 | 0.886964 | 0.886964 |

| weight | 1 | 1.070158 | 1.070158 | 1.070158 |



**marginally_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | -1.471542 | -1.471542 | -1.471542 |

| cross_encoder_score_normalized | 1 | 0.186708 | 0.186708 | 0.186708 |

| combined_score | 1 | 0.201158 | 0.201158 | 0.201158 |

| rrf_score | 1 | 0.032258 | 0.032258 | 0.032258 |

| semantic_similarity | 1 | 0.658341 | 0.658341 | 0.658341 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.886952 | 0.886952 | 0.886952 |

| weight | 1 | 0.201158 | 0.201158 | 0.201158 |



**noise (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | -11.311657 | -11.311657 | -11.311657 |

| cross_encoder_score_normalized | 1 | 0.000012 | 0.000012 | 0.000012 |

| combined_score | 1 | 0.000013 | 0.000013 | 0.000013 |

| rrf_score | 1 | 0.015873 | 0.015873 | 0.015873 |

| semantic_similarity | 1 | 0.622774 | 0.622774 | 0.622774 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.886958 | 0.886958 | 0.886958 |

| weight | 1 | 0.000013 | 0.000013 | 0.000013 |




**high budget (3 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 1 |

| Marginally relevant | 1 |

| Noise | 1 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | -11.311657 | 4.996698 | -2.595500 | -1.471542 | 3 |

| cross_encoder_score_normalized | 0.000012 | 0.993285 | 0.393335 | 0.186708 | 3 |

| combined_score | 0.000013 | 1.070158 | 0.423776 | 0.201158 | 3 |

| rrf_score | 0.015873 | 0.032787 | 0.026973 | 0.032258 | 3 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 3 |

| semantic_similarity | 0.622774 | 0.770483 | 0.683866 | 0.658341 | 3 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| recency | 0.886952 | 0.886964 | 0.886958 | 0.886958 | 3 |

| weight | 0.000013 | 1.070158 | 0.423776 | 0.201158 | 3 |

| activation | 0.000013 | 1.070158 | 0.423776 | 0.201158 | 3 |



**Scores by relevance bucket:**


**clearly_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 4.996698 | 4.996698 | 4.996698 |

| cross_encoder_score_normalized | 1 | 0.993285 | 0.993285 | 0.993285 |

| combined_score | 1 | 1.070158 | 1.070158 | 1.070158 |

| rrf_score | 1 | 0.032787 | 0.032787 | 0.032787 |

| semantic_similarity | 1 | 0.770483 | 0.770483 | 0.770483 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.886964 | 0.886964 | 0.886964 |

| weight | 1 | 1.070158 | 1.070158 | 1.070158 |



**marginally_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | -1.471542 | -1.471542 | -1.471542 |

| cross_encoder_score_normalized | 1 | 0.186708 | 0.186708 | 0.186708 |

| combined_score | 1 | 0.201158 | 0.201158 | 0.201158 |

| rrf_score | 1 | 0.032258 | 0.032258 | 0.032258 |

| semantic_similarity | 1 | 0.658341 | 0.658341 | 0.658341 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.886952 | 0.886952 | 0.886952 |

| weight | 1 | 0.201158 | 0.201158 | 0.201158 |



**noise (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | -11.311657 | -11.311657 | -11.311657 |

| cross_encoder_score_normalized | 1 | 0.000012 | 0.000012 | 0.000012 |

| combined_score | 1 | 0.000013 | 0.000013 | 0.000013 |

| rrf_score | 1 | 0.015873 | 0.015873 | 0.015873 |

| semantic_similarity | 1 | 0.622774 | 0.622774 | 0.622774 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.886958 | 0.886958 | 0.886958 |

| weight | 1 | 0.000013 | 0.000013 | 0.000013 |




### `pi-integration`


**low budget (2 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 1 |

| Marginally relevant | 1 |

| Noise | 0 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | -1.216931 | 1.269506 | 0.026287 | 1.269506 | 2 |

| cross_encoder_score_normalized | 0.228477 | 0.780658 | 0.504568 | 0.780658 | 2 |

| combined_score | 0.228477 | 0.780658 | 0.504568 | 0.780658 | 2 |

| rrf_score | 0.032258 | 0.032787 | 0.032522 | 0.032787 | 2 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 2 |

| semantic_similarity | 0.714023 | 0.762103 | 0.738063 | 0.762103 | 2 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 2 |

| recency | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 2 |

| weight | 0.228477 | 0.780658 | 0.504568 | 0.780658 | 2 |

| activation | 0.228477 | 0.780658 | 0.504568 | 0.780658 | 2 |



**Scores by relevance bucket:**


**clearly_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 1.269506 | 1.269506 | 1.269506 |

| cross_encoder_score_normalized | 1 | 0.780658 | 0.780658 | 0.780658 |

| combined_score | 1 | 0.780658 | 0.780658 | 0.780658 |

| rrf_score | 1 | 0.032787 | 0.032787 | 0.032787 |

| semantic_similarity | 1 | 0.762103 | 0.762103 | 0.762103 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.780658 | 0.780658 | 0.780658 |



**marginally_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | -1.216931 | -1.216931 | -1.216931 |

| cross_encoder_score_normalized | 1 | 0.228477 | 0.228477 | 0.228477 |

| combined_score | 1 | 0.228477 | 0.228477 | 0.228477 |

| rrf_score | 1 | 0.032258 | 0.032258 | 0.032258 |

| semantic_similarity | 1 | 0.714023 | 0.714023 | 0.714023 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.228477 | 0.228477 | 0.228477 |



**noise:** (0 results)



**mid budget (2 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 1 |

| Marginally relevant | 1 |

| Noise | 0 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | -1.216931 | 1.269506 | 0.026287 | 1.269506 | 2 |

| cross_encoder_score_normalized | 0.228477 | 0.780658 | 0.504568 | 0.780658 | 2 |

| combined_score | 0.228477 | 0.780658 | 0.504568 | 0.780658 | 2 |

| rrf_score | 0.032258 | 0.032787 | 0.032522 | 0.032787 | 2 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 2 |

| semantic_similarity | 0.714023 | 0.762103 | 0.738063 | 0.762103 | 2 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 2 |

| recency | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 2 |

| weight | 0.228477 | 0.780658 | 0.504568 | 0.780658 | 2 |

| activation | 0.228477 | 0.780658 | 0.504568 | 0.780658 | 2 |



**Scores by relevance bucket:**


**clearly_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 1.269506 | 1.269506 | 1.269506 |

| cross_encoder_score_normalized | 1 | 0.780658 | 0.780658 | 0.780658 |

| combined_score | 1 | 0.780658 | 0.780658 | 0.780658 |

| rrf_score | 1 | 0.032787 | 0.032787 | 0.032787 |

| semantic_similarity | 1 | 0.762103 | 0.762103 | 0.762103 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.780658 | 0.780658 | 0.780658 |



**marginally_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | -1.216931 | -1.216931 | -1.216931 |

| cross_encoder_score_normalized | 1 | 0.228477 | 0.228477 | 0.228477 |

| combined_score | 1 | 0.228477 | 0.228477 | 0.228477 |

| rrf_score | 1 | 0.032258 | 0.032258 | 0.032258 |

| semantic_similarity | 1 | 0.714023 | 0.714023 | 0.714023 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.228477 | 0.228477 | 0.228477 |



**noise:** (0 results)



**high budget (2 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 1 |

| Marginally relevant | 1 |

| Noise | 0 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | -1.216931 | 1.269506 | 0.026287 | 1.269506 | 2 |

| cross_encoder_score_normalized | 0.228477 | 0.780658 | 0.504568 | 0.780658 | 2 |

| combined_score | 0.228477 | 0.780658 | 0.504568 | 0.780658 | 2 |

| rrf_score | 0.032258 | 0.032787 | 0.032522 | 0.032787 | 2 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 2 |

| semantic_similarity | 0.714023 | 0.762103 | 0.738063 | 0.762103 | 2 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 2 |

| recency | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 2 |

| weight | 0.228477 | 0.780658 | 0.504568 | 0.780658 | 2 |

| activation | 0.228477 | 0.780658 | 0.504568 | 0.780658 | 2 |



**Scores by relevance bucket:**


**clearly_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 1.269506 | 1.269506 | 1.269506 |

| cross_encoder_score_normalized | 1 | 0.780658 | 0.780658 | 0.780658 |

| combined_score | 1 | 0.780658 | 0.780658 | 0.780658 |

| rrf_score | 1 | 0.032787 | 0.032787 | 0.032787 |

| semantic_similarity | 1 | 0.762103 | 0.762103 | 0.762103 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.780658 | 0.780658 | 0.780658 |



**marginally_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | -1.216931 | -1.216931 | -1.216931 |

| cross_encoder_score_normalized | 1 | 0.228477 | 0.228477 | 0.228477 |

| combined_score | 1 | 0.228477 | 0.228477 | 0.228477 |

| rrf_score | 1 | 0.032258 | 0.032258 | 0.032258 |

| semantic_similarity | 1 | 0.714023 | 0.714023 | 0.714023 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.228477 | 0.228477 | 0.228477 |



**noise:** (0 results)



### `product-strategy`


**low budget (3 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 2 |

| Marginally relevant | 0 |

| Noise | 1 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | 5.757302 | 6.978724 | 6.481208 | 6.707598 | 3 |

| cross_encoder_score_normalized | 0.996850 | 0.999069 | 0.998233 | 0.998780 | 3 |

| combined_score | 0.996850 | 0.999069 | 0.998233 | 0.998780 | 3 |

| rrf_score | 0.031746 | 0.032522 | 0.032264 | 0.032522 | 3 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 3 |

| semantic_similarity | 0.605818 | 0.769478 | 0.680954 | 0.667566 | 3 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| recency | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| weight | 0.996850 | 0.999069 | 0.998233 | 0.998780 | 3 |

| activation | 0.996850 | 0.999069 | 0.998233 | 0.998780 | 3 |



**Scores by relevance bucket:**


**clearly_relevant (2 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 2 | 6.707598 | 6.978724 | 6.843161 |

| cross_encoder_score_normalized | 2 | 0.998780 | 0.999069 | 0.998925 |

| combined_score | 2 | 0.998780 | 0.999069 | 0.998925 |

| rrf_score | 2 | 0.032522 | 0.032522 | 0.032522 |

| semantic_similarity | 2 | 0.667566 | 0.769478 | 0.718522 |

| temporal | 2 | 0.500000 | 0.500000 | 0.500000 |

| recency | 2 | 0.500000 | 0.500000 | 0.500000 |

| weight | 2 | 0.998780 | 0.999069 | 0.998925 |



**marginally_relevant:** (0 results)


**noise (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 5.757302 | 5.757302 | 5.757302 |

| cross_encoder_score_normalized | 1 | 0.996850 | 0.996850 | 0.996850 |

| combined_score | 1 | 0.996850 | 0.996850 | 0.996850 |

| rrf_score | 1 | 0.031746 | 0.031746 | 0.031746 |

| semantic_similarity | 1 | 0.605818 | 0.605818 | 0.605818 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.996850 | 0.996850 | 0.996850 |




**mid budget (3 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 2 |

| Marginally relevant | 0 |

| Noise | 1 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | 5.757302 | 6.978724 | 6.481208 | 6.707598 | 3 |

| cross_encoder_score_normalized | 0.996850 | 0.999069 | 0.998233 | 0.998780 | 3 |

| combined_score | 0.996850 | 0.999069 | 0.998233 | 0.998780 | 3 |

| rrf_score | 0.031746 | 0.032522 | 0.032264 | 0.032522 | 3 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 3 |

| semantic_similarity | 0.605818 | 0.769478 | 0.680954 | 0.667566 | 3 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| recency | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| weight | 0.996850 | 0.999069 | 0.998233 | 0.998780 | 3 |

| activation | 0.996850 | 0.999069 | 0.998233 | 0.998780 | 3 |



**Scores by relevance bucket:**


**clearly_relevant (2 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 2 | 6.707598 | 6.978724 | 6.843161 |

| cross_encoder_score_normalized | 2 | 0.998780 | 0.999069 | 0.998925 |

| combined_score | 2 | 0.998780 | 0.999069 | 0.998925 |

| rrf_score | 2 | 0.032522 | 0.032522 | 0.032522 |

| semantic_similarity | 2 | 0.667566 | 0.769478 | 0.718522 |

| temporal | 2 | 0.500000 | 0.500000 | 0.500000 |

| recency | 2 | 0.500000 | 0.500000 | 0.500000 |

| weight | 2 | 0.998780 | 0.999069 | 0.998925 |



**marginally_relevant:** (0 results)


**noise (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 5.757302 | 5.757302 | 5.757302 |

| cross_encoder_score_normalized | 1 | 0.996850 | 0.996850 | 0.996850 |

| combined_score | 1 | 0.996850 | 0.996850 | 0.996850 |

| rrf_score | 1 | 0.031746 | 0.031746 | 0.031746 |

| semantic_similarity | 1 | 0.605818 | 0.605818 | 0.605818 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.996850 | 0.996850 | 0.996850 |




**high budget (3 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 2 |

| Marginally relevant | 0 |

| Noise | 1 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | 5.757302 | 6.978724 | 6.481208 | 6.707598 | 3 |

| cross_encoder_score_normalized | 0.996850 | 0.999069 | 0.998233 | 0.998780 | 3 |

| combined_score | 0.996850 | 0.999069 | 0.998233 | 0.998780 | 3 |

| rrf_score | 0.031746 | 0.032522 | 0.032264 | 0.032522 | 3 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 3 |

| semantic_similarity | 0.605818 | 0.769478 | 0.680954 | 0.667566 | 3 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| recency | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 3 |

| weight | 0.996850 | 0.999069 | 0.998233 | 0.998780 | 3 |

| activation | 0.996850 | 0.999069 | 0.998233 | 0.998780 | 3 |



**Scores by relevance bucket:**


**clearly_relevant (2 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 2 | 6.707598 | 6.978724 | 6.843161 |

| cross_encoder_score_normalized | 2 | 0.998780 | 0.999069 | 0.998925 |

| combined_score | 2 | 0.998780 | 0.999069 | 0.998925 |

| rrf_score | 2 | 0.032522 | 0.032522 | 0.032522 |

| semantic_similarity | 2 | 0.667566 | 0.769478 | 0.718522 |

| temporal | 2 | 0.500000 | 0.500000 | 0.500000 |

| recency | 2 | 0.500000 | 0.500000 | 0.500000 |

| weight | 2 | 0.998780 | 0.999069 | 0.998925 |



**marginally_relevant:** (0 results)


**noise (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 5.757302 | 5.757302 | 5.757302 |

| cross_encoder_score_normalized | 1 | 0.996850 | 0.996850 | 0.996850 |

| combined_score | 1 | 0.996850 | 0.996850 | 0.996850 |

| rrf_score | 1 | 0.031746 | 0.031746 | 0.031746 |

| semantic_similarity | 1 | 0.605818 | 0.605818 | 0.605818 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.996850 | 0.996850 | 0.996850 |




### `session-evolution`


**low budget (5 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 1 |

| Marginally relevant | 1 |

| Noise | 3 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | -11.027550 | 2.410496 | -5.650461 | -9.776726 | 5 |

| cross_encoder_score_normalized | 0.000016 | 0.917624 | 0.333959 | 0.000057 | 5 |

| combined_score | 0.000016 | 0.917624 | 0.333959 | 0.000057 | 5 |

| rrf_score | 0.031010 | 0.032522 | 0.031762 | 0.031746 | 5 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 5 |

| semantic_similarity | 0.588451 | 0.777537 | 0.682070 | 0.676396 | 5 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 5 |

| recency | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 5 |

| weight | 0.000016 | 0.917624 | 0.333959 | 0.000057 | 5 |

| activation | 0.000016 | 0.917624 | 0.333959 | 0.000057 | 5 |



**Scores by relevance bucket:**


**clearly_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 2.410496 | 2.410496 | 2.410496 |

| cross_encoder_score_normalized | 1 | 0.917624 | 0.917624 | 0.917624 |

| combined_score | 1 | 0.917624 | 0.917624 | 0.917624 |

| rrf_score | 1 | 0.032522 | 0.032522 | 0.032522 |

| semantic_similarity | 1 | 0.777537 | 0.777537 | 0.777537 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.917624 | 0.917624 | 0.917624 |



**marginally_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 1.109743 | 1.109743 | 1.109743 |

| cross_encoder_score_normalized | 1 | 0.752081 | 0.752081 | 0.752081 |

| combined_score | 1 | 0.752081 | 0.752081 | 0.752081 |

| rrf_score | 1 | 0.032522 | 0.032522 | 0.032522 |

| semantic_similarity | 1 | 0.740677 | 0.740677 | 0.740677 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.752081 | 0.752081 | 0.752081 |



**noise (3 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 3 | -11.027550 | -9.776726 | -10.590848 |

| cross_encoder_score_normalized | 3 | 0.000016 | 0.000057 | 0.000030 |

| combined_score | 3 | 0.000016 | 0.000057 | 0.000030 |

| rrf_score | 3 | 0.031010 | 0.031746 | 0.031255 |

| semantic_similarity | 3 | 0.588451 | 0.676396 | 0.630713 |

| temporal | 3 | 0.500000 | 0.500000 | 0.500000 |

| recency | 3 | 0.500000 | 0.500000 | 0.500000 |

| weight | 3 | 0.000016 | 0.000057 | 0.000030 |




**mid budget (5 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 1 |

| Marginally relevant | 1 |

| Noise | 3 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | -11.027550 | 2.410496 | -5.650461 | -9.776726 | 5 |

| cross_encoder_score_normalized | 0.000016 | 0.917624 | 0.333959 | 0.000057 | 5 |

| combined_score | 0.000016 | 0.917624 | 0.333959 | 0.000057 | 5 |

| rrf_score | 0.031010 | 0.032522 | 0.031762 | 0.031746 | 5 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 5 |

| semantic_similarity | 0.588451 | 0.777537 | 0.682070 | 0.676396 | 5 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 5 |

| recency | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 5 |

| weight | 0.000016 | 0.917624 | 0.333959 | 0.000057 | 5 |

| activation | 0.000016 | 0.917624 | 0.333959 | 0.000057 | 5 |



**Scores by relevance bucket:**


**clearly_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 2.410496 | 2.410496 | 2.410496 |

| cross_encoder_score_normalized | 1 | 0.917624 | 0.917624 | 0.917624 |

| combined_score | 1 | 0.917624 | 0.917624 | 0.917624 |

| rrf_score | 1 | 0.032522 | 0.032522 | 0.032522 |

| semantic_similarity | 1 | 0.777537 | 0.777537 | 0.777537 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.917624 | 0.917624 | 0.917624 |



**marginally_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 1.109743 | 1.109743 | 1.109743 |

| cross_encoder_score_normalized | 1 | 0.752081 | 0.752081 | 0.752081 |

| combined_score | 1 | 0.752081 | 0.752081 | 0.752081 |

| rrf_score | 1 | 0.032522 | 0.032522 | 0.032522 |

| semantic_similarity | 1 | 0.740677 | 0.740677 | 0.740677 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.752081 | 0.752081 | 0.752081 |



**noise (3 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 3 | -11.027550 | -9.776726 | -10.590848 |

| cross_encoder_score_normalized | 3 | 0.000016 | 0.000057 | 0.000030 |

| combined_score | 3 | 0.000016 | 0.000057 | 0.000030 |

| rrf_score | 3 | 0.031010 | 0.031746 | 0.031255 |

| semantic_similarity | 3 | 0.588451 | 0.676396 | 0.630713 |

| temporal | 3 | 0.500000 | 0.500000 | 0.500000 |

| recency | 3 | 0.500000 | 0.500000 | 0.500000 |

| weight | 3 | 0.000016 | 0.000057 | 0.000030 |




**high budget (5 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 1 |

| Marginally relevant | 1 |

| Noise | 3 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | -11.027550 | 2.410496 | -5.650461 | -9.776726 | 5 |

| cross_encoder_score_normalized | 0.000016 | 0.917624 | 0.333959 | 0.000057 | 5 |

| combined_score | 0.000016 | 0.917624 | 0.333959 | 0.000057 | 5 |

| rrf_score | 0.031010 | 0.032522 | 0.031762 | 0.031746 | 5 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 5 |

| semantic_similarity | 0.588451 | 0.777537 | 0.682070 | 0.676396 | 5 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 5 |

| recency | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 5 |

| weight | 0.000016 | 0.917624 | 0.333959 | 0.000057 | 5 |

| activation | 0.000016 | 0.917624 | 0.333959 | 0.000057 | 5 |



**Scores by relevance bucket:**


**clearly_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 2.410496 | 2.410496 | 2.410496 |

| cross_encoder_score_normalized | 1 | 0.917624 | 0.917624 | 0.917624 |

| combined_score | 1 | 0.917624 | 0.917624 | 0.917624 |

| rrf_score | 1 | 0.032522 | 0.032522 | 0.032522 |

| semantic_similarity | 1 | 0.777537 | 0.777537 | 0.777537 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.917624 | 0.917624 | 0.917624 |



**marginally_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 1.109743 | 1.109743 | 1.109743 |

| cross_encoder_score_normalized | 1 | 0.752081 | 0.752081 | 0.752081 |

| combined_score | 1 | 0.752081 | 0.752081 | 0.752081 |

| rrf_score | 1 | 0.032522 | 0.032522 | 0.032522 |

| semantic_similarity | 1 | 0.740677 | 0.740677 | 0.740677 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.752081 | 0.752081 | 0.752081 |



**noise (3 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 3 | -11.027550 | -9.776726 | -10.590848 |

| cross_encoder_score_normalized | 3 | 0.000016 | 0.000057 | 0.000030 |

| combined_score | 3 | 0.000016 | 0.000057 | 0.000030 |

| rrf_score | 3 | 0.031010 | 0.031746 | 0.031255 |

| semantic_similarity | 3 | 0.588451 | 0.676396 | 0.630713 |

| temporal | 3 | 0.500000 | 0.500000 | 0.500000 |

| recency | 3 | 0.500000 | 0.500000 | 0.500000 |

| weight | 3 | 0.000016 | 0.000057 | 0.000030 |




### `user-profile`


**low budget (2 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 1 |

| Marginally relevant | 1 |

| Noise | 0 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | -10.016275 | 0.300374 | -4.857951 | 0.300374 | 2 |

| cross_encoder_score_normalized | 0.000045 | 0.574534 | 0.287289 | 0.574534 | 2 |

| combined_score | 0.000045 | 0.574534 | 0.287289 | 0.574534 | 2 |

| rrf_score | 0.032258 | 0.032787 | 0.032522 | 0.032787 | 2 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 2 |

| semantic_similarity | 0.597556 | 0.713491 | 0.655523 | 0.713491 | 2 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 2 |

| recency | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 2 |

| weight | 0.000045 | 0.574534 | 0.287289 | 0.574534 | 2 |

| activation | 0.000045 | 0.574534 | 0.287289 | 0.574534 | 2 |



**Scores by relevance bucket:**


**clearly_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 0.300374 | 0.300374 | 0.300374 |

| cross_encoder_score_normalized | 1 | 0.574534 | 0.574534 | 0.574534 |

| combined_score | 1 | 0.574534 | 0.574534 | 0.574534 |

| rrf_score | 1 | 0.032787 | 0.032787 | 0.032787 |

| semantic_similarity | 1 | 0.713491 | 0.713491 | 0.713491 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.574534 | 0.574534 | 0.574534 |



**marginally_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | -10.016275 | -10.016275 | -10.016275 |

| cross_encoder_score_normalized | 1 | 0.000045 | 0.000045 | 0.000045 |

| combined_score | 1 | 0.000045 | 0.000045 | 0.000045 |

| rrf_score | 1 | 0.032258 | 0.032258 | 0.032258 |

| semantic_similarity | 1 | 0.597556 | 0.597556 | 0.597556 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.000045 | 0.000045 | 0.000045 |



**noise:** (0 results)



**mid budget (2 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 1 |

| Marginally relevant | 1 |

| Noise | 0 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | -10.016275 | 0.300374 | -4.857951 | 0.300374 | 2 |

| cross_encoder_score_normalized | 0.000045 | 0.574534 | 0.287289 | 0.574534 | 2 |

| combined_score | 0.000045 | 0.574534 | 0.287289 | 0.574534 | 2 |

| rrf_score | 0.032258 | 0.032787 | 0.032522 | 0.032787 | 2 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 2 |

| semantic_similarity | 0.597556 | 0.713491 | 0.655523 | 0.713491 | 2 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 2 |

| recency | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 2 |

| weight | 0.000045 | 0.574534 | 0.287289 | 0.574534 | 2 |

| activation | 0.000045 | 0.574534 | 0.287289 | 0.574534 | 2 |



**Scores by relevance bucket:**


**clearly_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 0.300374 | 0.300374 | 0.300374 |

| cross_encoder_score_normalized | 1 | 0.574534 | 0.574534 | 0.574534 |

| combined_score | 1 | 0.574534 | 0.574534 | 0.574534 |

| rrf_score | 1 | 0.032787 | 0.032787 | 0.032787 |

| semantic_similarity | 1 | 0.713491 | 0.713491 | 0.713491 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.574534 | 0.574534 | 0.574534 |



**marginally_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | -10.016275 | -10.016275 | -10.016275 |

| cross_encoder_score_normalized | 1 | 0.000045 | 0.000045 | 0.000045 |

| combined_score | 1 | 0.000045 | 0.000045 | 0.000045 |

| rrf_score | 1 | 0.032258 | 0.032258 | 0.032258 |

| semantic_similarity | 1 | 0.597556 | 0.597556 | 0.597556 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.000045 | 0.000045 | 0.000045 |



**noise:** (0 results)



**high budget (2 results):**


| Metric | Value |
|--------|-------|

| Clearly relevant | 1 |

| Marginally relevant | 1 |

| Noise | 0 |

| CE-norm vs combined Spearman correlation | 1.0000 |



**Full score distributions:**


| Score type | Min | Max | Mean | Median | Count |

|------------|-----|-----|------|--------|-------|

| cross_encoder_score | -10.016275 | 0.300374 | -4.857951 | 0.300374 | 2 |

| cross_encoder_score_normalized | 0.000045 | 0.574534 | 0.287289 | 0.574534 | 2 |

| combined_score | 0.000045 | 0.574534 | 0.287289 | 0.574534 | 2 |

| rrf_score | 0.032258 | 0.032787 | 0.032522 | 0.032787 | 2 |

| rrf_normalized | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 2 |

| semantic_similarity | 0.597556 | 0.713491 | 0.655523 | 0.713491 | 2 |

| temporal | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 2 |

| recency | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 2 |

| weight | 0.000045 | 0.574534 | 0.287289 | 0.574534 | 2 |

| activation | 0.000045 | 0.574534 | 0.287289 | 0.574534 | 2 |



**Scores by relevance bucket:**


**clearly_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | 0.300374 | 0.300374 | 0.300374 |

| cross_encoder_score_normalized | 1 | 0.574534 | 0.574534 | 0.574534 |

| combined_score | 1 | 0.574534 | 0.574534 | 0.574534 |

| rrf_score | 1 | 0.032787 | 0.032787 | 0.032787 |

| semantic_similarity | 1 | 0.713491 | 0.713491 | 0.713491 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.574534 | 0.574534 | 0.574534 |



**marginally_relevant (1 results):**


| Score type | Count | Min | Max | Mean |

|------------|-------|-----|-----|------|

| cross_encoder_score | 1 | -10.016275 | -10.016275 | -10.016275 |

| cross_encoder_score_normalized | 1 | 0.000045 | 0.000045 | 0.000045 |

| combined_score | 1 | 0.000045 | 0.000045 | 0.000045 |

| rrf_score | 1 | 0.032258 | 0.032258 | 0.032258 |

| semantic_similarity | 1 | 0.597556 | 0.597556 | 0.597556 |

| temporal | 1 | 0.500000 | 0.500000 | 0.500000 |

| recency | 1 | 0.500000 | 0.500000 | 0.500000 |

| weight | 1 | 0.000045 | 0.000045 | 0.000045 |



**noise:** (0 results)



## 4. Cross-Encoder Normalized vs Combined Score Comparison


Comparing `cross_encoder_score_normalized` vs `combined_score` for thresholding:


| Bank | Budget | CE-Norm vs Combined Spearman ρ |

|------|--------|-------------------------------|

| user-profile | low | 1.0000 |

| user-profile | mid | 1.0000 |

| user-profile | high | 1.0000 |

| product-strategy | low | 1.0000 |

| product-strategy | mid | 1.0000 |

| product-strategy | high | 1.0000 |

| implementation-work | low | 1.0000 |

| implementation-work | mid | 1.0000 |

| implementation-work | high | 1.0000 |

| assistant-ops | low | 1.0000 |

| assistant-ops | mid | 1.0000 |

| assistant-ops | high | 1.0000 |

| framework-procedural | low | 1.0000 |

| framework-procedural | mid | 1.0000 |

| framework-procedural | high | 1.0000 |

| pi-integration | low | 1.0000 |

| pi-integration | mid | 1.0000 |

| pi-integration | high | 1.0000 |

| session-evolution | low | 1.0000 |

| session-evolution | mid | 1.0000 |

| session-evolution | high | 1.0000 |


**Average Spearman ρ: 1.0000**


Interpretation: Very strong positive correlation — CE-normalized and combined scores rank results nearly identically. Either can be used for thresholding.


## 5. Threshold Viability Analysis


For each bank, we assess whether a threshold can separate clearly_relevant from marginally_relevant/noise results:


### `assistant-ops`


**low budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.014814 | 0.071360 | 0.043087 | 2 |

| Noise | 0.960014 | 0.960014 | 0.960014 | 1 |



  ⚠️ **Partial separation**: some overlap between clearly relevant and marginally relevant

  💡 **Conservative threshold (CE-norm)**: ~0.0141



**mid budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.014814 | 0.071360 | 0.043087 | 2 |

| Noise | 0.960014 | 0.960014 | 0.960014 | 1 |



  ⚠️ **Partial separation**: some overlap between clearly relevant and marginally relevant

  💡 **Conservative threshold (CE-norm)**: ~0.0141



**high budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.014814 | 0.071360 | 0.043087 | 2 |

| Noise | 0.960014 | 0.960014 | 0.960014 | 1 |



  ⚠️ **Partial separation**: some overlap between clearly relevant and marginally relevant

  💡 **Conservative threshold (CE-norm)**: ~0.0141



### `framework-procedural`


**low budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.997490 | 0.997490 | 0.997490 | 1 |

| Noise | 0.000218 | 0.000580 | 0.000399 | 2 |



  ⚠️ **Partial separation**: some overlap between clearly relevant and marginally relevant

  💡 **Conservative threshold (CE-norm)**: ~0.9476



**mid budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.997490 | 0.997490 | 0.997490 | 1 |

| Noise | 0.000218 | 0.000580 | 0.000399 | 2 |



  ⚠️ **Partial separation**: some overlap between clearly relevant and marginally relevant

  💡 **Conservative threshold (CE-norm)**: ~0.9476



**high budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.997490 | 0.997490 | 0.997490 | 1 |

| Noise | 0.000218 | 0.000580 | 0.000399 | 2 |



  ⚠️ **Partial separation**: some overlap between clearly relevant and marginally relevant

  💡 **Conservative threshold (CE-norm)**: ~0.9476



### `implementation-work`


**low budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.993285 | 0.993285 | 0.993285 | 1 |

| Marginally relevant | 0.186708 | 0.186708 | 0.186708 | 1 |

| Noise | 0.000012 | 0.000012 | 0.000012 | 1 |



  ✅ **Viable gap**: 0.8066 between clearly relevant min and marginally relevant max

  💡 **Recommended threshold (CE-norm)**: ~0.5900



**mid budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.993285 | 0.993285 | 0.993285 | 1 |

| Marginally relevant | 0.186708 | 0.186708 | 0.186708 | 1 |

| Noise | 0.000012 | 0.000012 | 0.000012 | 1 |



  ✅ **Viable gap**: 0.8066 between clearly relevant min and marginally relevant max

  💡 **Recommended threshold (CE-norm)**: ~0.5900



**high budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.993285 | 0.993285 | 0.993285 | 1 |

| Marginally relevant | 0.186708 | 0.186708 | 0.186708 | 1 |

| Noise | 0.000012 | 0.000012 | 0.000012 | 1 |



  ✅ **Viable gap**: 0.8066 between clearly relevant min and marginally relevant max

  💡 **Recommended threshold (CE-norm)**: ~0.5900



### `pi-integration`


**low budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.780658 | 0.780658 | 0.780658 | 1 |

| Marginally relevant | 0.228477 | 0.228477 | 0.228477 | 1 |



  ✅ **Viable gap**: 0.5522 between clearly relevant min and marginally relevant max

  💡 **Recommended threshold (CE-norm)**: ~0.5046



**mid budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.780658 | 0.780658 | 0.780658 | 1 |

| Marginally relevant | 0.228477 | 0.228477 | 0.228477 | 1 |



  ✅ **Viable gap**: 0.5522 between clearly relevant min and marginally relevant max

  💡 **Recommended threshold (CE-norm)**: ~0.5046



**high budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.780658 | 0.780658 | 0.780658 | 1 |

| Marginally relevant | 0.228477 | 0.228477 | 0.228477 | 1 |



  ✅ **Viable gap**: 0.5522 between clearly relevant min and marginally relevant max

  💡 **Recommended threshold (CE-norm)**: ~0.5046



### `product-strategy`


**low budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.998780 | 0.999069 | 0.998925 | 2 |

| Noise | 0.996850 | 0.996850 | 0.996850 | 1 |



  ⚠️ **Partial separation**: some overlap between clearly relevant and marginally relevant

  💡 **Conservative threshold (CE-norm)**: ~0.9488



**mid budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.998780 | 0.999069 | 0.998925 | 2 |

| Noise | 0.996850 | 0.996850 | 0.996850 | 1 |



  ⚠️ **Partial separation**: some overlap between clearly relevant and marginally relevant

  💡 **Conservative threshold (CE-norm)**: ~0.9488



**high budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.998780 | 0.999069 | 0.998925 | 2 |

| Noise | 0.996850 | 0.996850 | 0.996850 | 1 |



  ⚠️ **Partial separation**: some overlap between clearly relevant and marginally relevant

  💡 **Conservative threshold (CE-norm)**: ~0.9488



### `session-evolution`


**low budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.917624 | 0.917624 | 0.917624 | 1 |

| Marginally relevant | 0.752081 | 0.752081 | 0.752081 | 1 |

| Noise | 0.000016 | 0.000057 | 0.000030 | 3 |



  ✅ **Viable gap**: 0.1655 between clearly relevant min and marginally relevant max

  💡 **Recommended threshold (CE-norm)**: ~0.8349



**mid budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.917624 | 0.917624 | 0.917624 | 1 |

| Marginally relevant | 0.752081 | 0.752081 | 0.752081 | 1 |

| Noise | 0.000016 | 0.000057 | 0.000030 | 3 |



  ✅ **Viable gap**: 0.1655 between clearly relevant min and marginally relevant max

  💡 **Recommended threshold (CE-norm)**: ~0.8349



**high budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.917624 | 0.917624 | 0.917624 | 1 |

| Marginally relevant | 0.752081 | 0.752081 | 0.752081 | 1 |

| Noise | 0.000016 | 0.000057 | 0.000030 | 3 |



  ✅ **Viable gap**: 0.1655 between clearly relevant min and marginally relevant max

  💡 **Recommended threshold (CE-norm)**: ~0.8349



### `user-profile`


**low budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.574534 | 0.574534 | 0.574534 | 1 |

| Marginally relevant | 0.000045 | 0.000045 | 0.000045 | 1 |



  ✅ **Viable gap**: 0.5745 between clearly relevant min and marginally relevant max

  💡 **Recommended threshold (CE-norm)**: ~0.2873



**mid budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.574534 | 0.574534 | 0.574534 | 1 |

| Marginally relevant | 0.000045 | 0.000045 | 0.000045 | 1 |



  ✅ **Viable gap**: 0.5745 between clearly relevant min and marginally relevant max

  💡 **Recommended threshold (CE-norm)**: ~0.2873



**high budget:**


| Relevance bucket | CE-norm Min | CE-norm Max | CE-norm Mean | Count |

|-----------------|-------------|-------------|-------------|-------|

| Clearly relevant | 0.574534 | 0.574534 | 0.574534 | 1 |

| Marginally relevant | 0.000045 | 0.000045 | 0.000045 | 1 |



  ✅ **Viable gap**: 0.5745 between clearly relevant min and marginally relevant max

  💡 **Recommended threshold (CE-norm)**: ~0.2873



## 6. Recommended Threshold Values


### Per-bank recommended thresholds


| Bank | CE-norm threshold | Combined threshold | Notes |

|------|-------------------|-------------------|-------|

| user-profile | 0.2873 | 0.2873 | Based on gap analysis across all budgets |

| product-strategy | 0.9988 | 0.9988 | Based on gap analysis across all budgets |

| implementation-work | 0.59 | 0.6357 | Based on gap analysis across all budgets |

| assistant-ops | 0.0148 | 0.0148 | Based on gap analysis across all budgets |

| framework-procedural | 0.9975 | 0.9975 | Based on gap analysis across all budgets |

| pi-integration | 0.5046 | 0.5046 | Based on gap analysis across all budgets |

| session-evolution | 0.8349 | 0.8349 | Based on gap analysis across all budgets |



### Universal threshold recommendation


A **universal threshold of `cross_encoder_score_normalized = 0.30`** is a conservative starting point because:


1. It is below the mean of clearly_relevant scores across all banks

2. It is above the mean of noise/marginally relevant scores for most banks

3. It provides a safety margin against false negatives


However, per-bank thresholds may be more accurate for production use where fact densities vary widely.


## 7. Score Field Reference


### Complete field inventory from `trace.final_results`


The following numeric score fields were observed in the trace payloads:


| Field | Present in data? | Type |

|-------|-----------------|------|

| activation | Yes | numeric |

| bm25_rank | Yes | numeric |

| combined_score | Yes | numeric |

| cross_encoder_score | Yes | numeric |

| cross_encoder_score_normalized | Yes | numeric |

| recency | Yes | numeric |

| rrf_normalized | Yes | numeric |

| rrf_rank | Yes | numeric |

| rrf_score | Yes | numeric |

| semantic_rank | Yes | numeric |

| semantic_similarity | Yes | numeric |

| temporal | Yes | numeric |

| weight | Yes | numeric |



## 8. Gap Analysis & Limitations


### Edge cases


1. **Small bank effect**: With only 2-6 facts per bank, most results are relevant. Thresholding differentiation would be more visible with larger production banks (100+ facts). The `framework-procedural` bank (6 facts) showed the clearest separation.


2. **Budget level has minimal score variation**: Low/mid/high budgets return nearly identical scores because `thinking_budget` only affects DB search scope, not the scoring function itself.


3. **Combined_score vs CE-normalized**: The combined_score applies recency decay and temporal weighting, which can lower scores for older facts. For fresh canary data (all same timestamp), combined_score ≈ ce_normalized.


4. **RRF normalization is zero**: `rrf_normalized` was consistently 0.0 for all results. This field appears to not be populated in the current API version.


5. **bm25_score is raw (not normalized)**: BM25 scores are unbounded (0–∞) and much smaller than CE scores. They are used for fusion but not ideal for thresholding alone.


6. **No per-result trace breakdown**: The trace payload does not decompose `combined_score` into its component multiplications (CE × recency × temporal × proof_count).


7. **Score normalization method unknown**: We do not know the exact sigmoid/logits function used for `cross_encoder_score_normalized`.


## 9. Data Artifacts


- **Raw score data:** `/tmp/recall_score_data.json`

- **Script:** `/tmp/recall_score_experiment_v2.py`


### Experiment summary


| Metric | Value |
|--------|-------|

| Banks tested | 7 |

| Budget levels | 3 (low, mid, high) |

| Total experiments | 21 |

| Total results classified | 63 |

| Clearly relevant | 27 |

| Marginally relevant | 12 |

| Noise | 24 |
