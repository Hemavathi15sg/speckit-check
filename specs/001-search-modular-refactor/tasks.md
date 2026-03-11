# Tasks: Search Module Refactoring

**Feature**: `001-search-modular-refactor`  
**Input**: Design documents from `/specs/001-search-modular-refactor/`  
**Prerequisites**: ✅ plan.md, ✅ spec.md, ✅ research.md, ✅ data-model.md, ✅ contracts/, ✅ quickstart.md

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1, US2, US3, US4)
- File paths are absolute from repository root

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create foundational structure for modular search package

- [X] T001 Create search/ package directory structure in recipe-manager/search/
- [X] T002 Create search/__init__.py with public API exports for backward compatibility
- [X] T003 [P] Create tests/unit/ directory for module-specific unit tests
- [X] T004 [P] Create tests/contract/ directory for interface contract tests
- [X] T005 [P] Create tests/integration/ directory for end-to-end pipeline tests

---

## Phase 2: Foundational (Blocking Prerequisites for All User Stories)

**Purpose**: Core infrastructure required before ANY user story implementation

**⚠️ CRITICAL**: Must complete before user story work begins

- [X] T006 Create search/types.py with all 5 dataclass definitions (SearchRequest, ValidatedSearchInput, FilteredRecipes, RankedResults, SearchResponse) per data-model.md
- [X] T007 Create search/constants.py extracting all 74 magic numbers from legacy search.py (VALID_CUISINES, VALID_DIETARY_RESTRICTIONS, MAX_CACHE_SIZE, CACHE_TTL_SECONDS, etc.)
- [X] T008 Create search/exceptions.py with ValidationError, FilteringError, AggregationError, FormattingError exception classes
- [X] T009 Update requirements.txt if typing_extensions needed for Python 3.11 compatibility
- [X] T010 Configure pytest.ini for coverage settings (--cov=search --cov-report=term-missing)
- [X] T011 Configure mypy.ini or pyproject.toml for strict type checking (python_version=3.11, strict=true)

**Checkpoint**: ✅ Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reliable Search for All Users (Priority: P1) 🎯 MVP

**Goal**: Fix Issue #447 - Zero crashes for users with `dietary_restrictions=None` (currently affects 30% of users)

**Independent Test**: Create test user with `dietary_restrictions=None`, execute search for "pasta", verify results returned without TypeError

**Why First**: Critical production bug affecting 30% of users. Search is unusable for affected users. MUST FIX IMMEDIATELY.

### Tests for User Story 1 (Write FIRST, ensure they FAIL before implementation)

- [X] T012 [P] [US1] Write unit test test_none_dietary_restrictions_normalized_to_empty_list in tests/unit/test_validation_module.py
- [X] T013 [P] [US1] Write unit test test_empty_dietary_restrictions_preserved in tests/unit/test_validation_module.py
- [X] T014 [P] [US1] Write unit test test_valid_dietary_restrictions_normalized in tests/unit/test_validation_module.py
- [X] T015 [P] [US1] Write unit test test_invalid_dietary_restriction_raises_error in tests/unit/test_validation_module.py
- [X] T016 [P] [US1] Write unit test test_duplicate_dietary_restrictions_removed in tests/unit/test_validation_module.py
- [X] T017 [P] [US1] Write unit test test_none_query_normalized_to_empty_string in tests/unit/test_validation_module.py
- [X] T018 [P] [US1] Write unit test test_query_trimmed_and_lowercased in tests/unit/test_validation_module.py
- [X] T019 [P] [US1] Write unit test test_query_truncated_if_too_long in tests/unit/test_validation_module.py
- [X] T020 [P] [US1] Write unit test test_invalid_cuisine_raises_error in tests/unit/test_validation_module.py
- [X] T021 [P] [US1] Write unit test test_valid_cuisine_normalized in tests/unit/test_validation_module.py
- [X] T022 [P] [US1] Write unit test test_prep_time_negative_raises_error in tests/unit/test_validation_module.py
- [X] T023 [P] [US1] Write unit test test_page_zero_raises_error in tests/unit/test_validation_module.py
- [X] T024 [P] [US1] Write unit test test_page_size_exceeds_max_raises_error in tests/unit/test_validation_module.py
- [X] T025 [P] [US1] Write unit test test_min_rating_out_of_range_raises_error in tests/unit/test_validation_module.py
- [X] T026 [P] [US1] Write unit test test_all_defaults_applied in tests/unit/test_validation_module.py
- [X] T027 [P] [US1] Write contract test test_contract_dietary_restrictions_never_none in tests/contract/test_validation_contract.py (100 random inputs)
- [X] T028 [P] [US1] Write contract test test_contract_all_required_fields_populated in tests/contract/test_validation_contract.py
- [X] T029 [P] [US1] Write contract test test_contract_immutability in tests/contract/test_validation_contract.py (verify frozen=True)

### Implementation for User Story 1

- [X] T030 [US1] Implement validate_search_request() function in search/validation_module.py (normalize None dietary_restrictions to [])
- [X] T031 [US1] Implement _validate_query() helper in search/validation_module.py (max 500 chars, trim, lowercase)
- [X] T032 [US1] Implement _validate_cuisine() helper in search/validation_module.py (check VALID_CUISINES set)
- [X] T033 [US1] Implement _validate_dietary_restrictions() helper in search/validation_module.py (CRITICAL: None → [], check VALID_DIETARY_RESTRICTIONS, remove duplicates)
- [X] T034 [US1] Implement _validate_prep_time() helper in search/validation_module.py (must be positive or None)
- [X] T035 [US1] Implement _validate_difficulty() helper in search/validation_module.py (must be easy/medium/hard or None)
- [X] T036 [US1] Implement _validate_min_rating() helper in search/validation_module.py (0.0-5.0 range, default 0.0)
- [X] T037 [US1] Implement _validate_pagination() helper in search/validation_module.py (page ≥1, page_size 1-200)
- [X] T038 [US1] Add logging for validation success and failures in search/validation_module.py
- [X] T039 [US1] Add performance timing measurement in search/validation_module.py (target P50 <5ms)

### Verification for User Story 1

- [X] T040 [US1] Run pytest tests/unit/test_validation_module.py --cov=search.validation_module (verify ≥80% coverage)
- [X] T041 [US1] Run pytest tests/contract/test_validation_contract.py (verify all contracts pass)
- [X] T042 [US1] Run mypy search/validation_module.py --strict (verify zero type errors)
- [X] T043 [US1] Run pylint search/validation_module.py (verify score ≥9.0/10)
- [X] T044 [US1] Verify module line count ≤300 lines (excluding comments/blank lines)
- [X] T045 [US1] Manual test: Create user with dietary_restrictions=None, search for "pasta", verify no TypeError

**Checkpoint**: ✅ User Story 1 complete - Issue #447 FIXED, validation module ready for production

**Acceptance Criteria**:
- ✅ SC-001: Zero crashes for dietary_restrictions=None (100% success rate)
- ✅ SC-002: Zero TypeError from validation module
- ✅ SC-008: Validation module achieves ≥80% coverage
- ✅ SC-011: mypy strict passes, pylint ≥9.0/10
- ✅ SC-012: validation_module ≤300 lines

---

## Phase 4: User Story 2 - Maintainable Codebase for Developers (Priority: P2)

**Goal**: Developers can modify filtering logic independently without navigating 1006-line monolith

**Independent Test**: Verify filtering_module.py is ≤300 lines, has no circular dependencies, passes independent unit tests with >80% coverage

**Why Second**: Current monolith unmaintainable. Refactoring enables parallel development and reduces cognitive load.

### Tests for User Story 2 (Write FIRST)

- [ ] T046 [P] [US2] Write unit test test_query_filter_matches_name in tests/unit/test_filtering_module.py
- [ ] T047 [P] [US2] Write unit test test_query_filter_matches_ingredient in tests/unit/test_filtering_module.py
- [ ] T048 [P] [US2] Write unit test test_query_filter_empty_returns_all in tests/unit/test_filtering_module.py
- [ ] T049 [P] [US2] Write unit test test_cuisine_filter_exact_match in tests/unit/test_filtering_module.py
- [ ] T050 [P] [US2] Write unit test test_cuisine_filter_none_returns_all in tests/unit/test_filtering_module.py
- [ ] T051 [P] [US2] Write unit test test_dietary_restrictions_all_required in tests/unit/test_filtering_module.py
- [ ] T052 [P] [US2] Write unit test test_dietary_restrictions_empty_returns_all in tests/unit/test_filtering_module.py
- [ ] T053 [P] [US2] Write unit test test_dietary_restrictions_never_none in tests/unit/test_filtering_module.py (verify Issue #447 prevented)
- [ ] T054 [P] [US2] Write unit test test_prep_time_filter_less_than_or_equal in tests/unit/test_filtering_module.py
- [ ] T055 [P] [US2] Write unit test test_prep_time_filter_none_returns_all in tests/unit/test_filtering_module.py
- [ ] T056 [P] [US2] Write unit test test_difficulty_filter_exact_match in tests/unit/test_filtering_module.py
- [ ] T057 [P] [US2] Write unit test test_rating_filter_greater_than_or_equal in tests/unit/test_filtering_module.py
- [ ] T058 [P] [US2] Write unit test test_combined_filters_all_criteria in tests/unit/test_filtering_module.py
- [ ] T059 [P] [US2] Write unit test test_short_circuit_on_empty_query in tests/unit/test_filtering_module.py
- [ ] T060 [P] [US2] Write unit test test_applied_filters_metadata in tests/unit/test_filtering_module.py
- [ ] T061 [P] [US2] Write contract test test_contract_returns_filtered_recipes_type in tests/contract/test_filtering_contract.py
- [ ] T062 [P] [US2] Write contract test test_contract_recipes_list_never_none in tests/contract/test_filtering_contract.py
- [ ] T063 [P] [US2] Write contract test test_contract_applied_filters_dict_never_none in tests/contract/test_filtering_contract.py
- [ ] T064 [P] [US2] Write contract test test_contract_duration_always_positive in tests/contract/test_filtering_contract.py
- [ ] T065 [P] [US2] Write contract test test_contract_total_before_filters_matches_input in tests/contract/test_filtering_contract.py
- [ ] T066 [P] [US2] Write integration test test_validation_to_filtering_pipeline in tests/integration/test_full_pipeline.py
- [ ] T067 [P] [US2] Write integration test test_issue_447_prevented_end_to_end in tests/integration/test_full_pipeline.py

### Implementation for User Story 2

- [ ] T068 [US2] Implement apply_filters() main function in search/filtering_module.py
- [ ] T069 [US2] Implement _filter_by_query() helper in search/filtering_module.py (substring match name + ingredients, short-circuit optimization)
- [ ] T070 [US2] Implement _filter_by_cuisine() helper in search/filtering_module.py (exact match)
- [ ] T071 [US2] Implement _filter_by_dietary_restrictions() helper in search/filtering_module.py (set intersection, ALL restrictions required)
- [ ] T072 [US2] Implement _filter_by_prep_time() helper in search/filtering_module.py (≤ max)
- [ ] T073 [US2] Implement _filter_by_difficulty() helper in search/filtering_module.py (exact match)
- [ ] T074 [US2] Implement _filter_by_rating() helper in search/filtering_module.py (≥ min)
- [ ] T075 [US2] Implement filter execution with optimal order (query → cuisine → dietary → prep_time → difficulty → rating)
- [ ] T076 [US2] Add short-circuit optimization (return early if recipes empty after any filter)
- [ ] T077 [US2] Add applied_filters metadata generation in search/filtering_module.py
- [ ] T078 [US2] Add logging for filtering operations in search/filtering_module.py
- [ ] T079 [US2] Add performance timing measurement in search/filtering_module.py (target P50 <20ms)
- [ ] T080 [US2] Remove deprecated filter functions from legacy search.py (filter_by_dietary_v1, filter_by_dietary_v2)

### Verification for User Story 2

- [ ] T081 [US2] Run pytest tests/unit/test_filtering_module.py --cov=search.filtering_module (verify ≥80% coverage)
- [ ] T082 [US2] Run pytest tests/contract/test_filtering_contract.py (verify all contracts pass)
- [ ] T083 [US2] Run pytest tests/integration/test_full_pipeline.py (verify validation→filtering pipeline works)
- [ ] T084 [US2] Run mypy search/filtering_module.py --strict (verify zero type errors)
- [ ] T085 [US2] Run pylint search/filtering_module.py (verify score ≥9.0/10)
- [ ] T086 [US2] Verify module line count ≤300 lines (excluding comments/blank lines)
- [ ] T087 [US2] Verify each filter function is <50 lines (single responsibility principle)

**Checkpoint**: ✅ User Story 2 complete - Filtering logic isolated, maintainable, independently testable

**Acceptance Criteria**:
- ✅ SC-008: Filtering module achieves ≥80% coverage
- ✅ SC-010: All deprecated filter functions removed
- ✅ SC-011: mypy strict passes, pylint ≥9.0/10
- ✅ SC-012: filtering_module ≤300 lines
- ✅ SC-013: Module understandable in ≤15 minutes

---

## Phase 5: User Story 3 - Fast and Reliable Search Results (Priority: P3)

**Goal**: Fix Issue #183 (cache memory leak), improve latency from 280ms to <100ms P50, achieve ≥60% cache hit rate

**Independent Test**: Run load test with 1000 concurrent searches for 1 hour, verify P95 ≤200ms and memory ≤50MB

**Why Third**: Performance improvements enhance UX and reduce costs, but less urgent than fixing crashes and maintainability

### Tests for User Story 3 (Write FIRST)

- [ ] T088 [P] [US3] Write unit test test_ranking_algorithm_text_relevance in tests/unit/test_aggregation_module.py
- [ ] T089 [P] [US3] Write unit test test_ranking_algorithm_quality_score in tests/unit/test_aggregation_module.py
- [ ] T090 [P] [US3] Write unit test test_ranking_algorithm_popularity_score in tests/unit/test_aggregation_module.py
- [ ] T091 [P] [US3] Write unit test test_ranking_algorithm_hybrid_score in tests/unit/test_aggregation_module.py
- [ ] T092 [P] [US3] Write unit test test_ranking_no_query_all_equal_text_relevance in tests/unit/test_aggregation_module.py
- [ ] T093 [P] [US3] Write unit test test_cache_hit_returns_cached_results in tests/unit/test_aggregation_module.py
- [ ] T094 [P] [US3] Write unit test test_cache_miss_computes_fresh_results in tests/unit/test_aggregation_module.py
- [ ] T095 [P] [US3] Write unit test test_cache_key_includes_all_filters in tests/unit/test_aggregation_module.py
- [ ] T096 [P] [US3] Write unit test test_cache_key_excludes_pagination in tests/unit/test_aggregation_module.py
- [ ] T097 [P] [US3] Write unit test test_cache_ttl_expires_old_entries in tests/unit/test_aggregation_module.py
- [ ] T098 [P] [US3] Write unit test test_cache_lru_eviction_at_max_size in tests/unit/test_aggregation_module.py (insert 1001 entries, verify only 1000 kept)
- [ ] T099 [P] [US3] Write unit test test_pagination_page_within_range in tests/unit/test_aggregation_module.py
- [ ] T100 [P] [US3] Write unit test test_pagination_page_beyond_range in tests/unit/test_aggregation_module.py
- [ ] T101 [P] [US3] Write unit test test_pagination_first_page in tests/unit/test_aggregation_module.py
- [ ] T102 [P] [US3] Write unit test test_total_pages_calculation in tests/unit/test_aggregation_module.py
- [ ] T103 [P] [US3] Write unit test test_total_pages_zero_for_no_results in tests/unit/test_aggregation_module.py
- [ ] T104 [P] [US3] Write unit test test_total_duration_includes_all_modules in tests/unit/test_aggregation_module.py
- [ ] T105 [P] [US3] Write contract test test_contract_returns_ranked_results_type in tests/contract/test_aggregation_contract.py
- [ ] T106 [P] [US3] Write contract test test_contract_recipes_list_never_none in tests/contract/test_aggregation_contract.py
- [ ] T107 [P] [US3] Write contract test test_contract_total_count_matches_filtered in tests/contract/test_aggregation_contract.py
- [ ] T108 [P] [US3] Write contract test test_contract_page_info_matches_input in tests/contract/test_aggregation_contract.py
- [ ] T109 [P] [US3] Write contract test test_contract_cache_hit_boolean in tests/contract/test_aggregation_contract.py
- [ ] T110 [P] [US3] Write contract test test_contract_ranking_duration_zero_on_cache_hit in tests/contract/test_aggregation_contract.py
- [ ] T111 [P] [US3] Write contract test test_contract_total_duration_always_positive in tests/contract/test_aggregation_contract.py
- [ ] T112 [P] [US3] Write integration test test_validation_filtering_aggregation_pipeline in tests/integration/test_full_pipeline.py
- [ ] T113 [P] [US3] Write integration test test_cache_persistence_across_calls in tests/integration/test_full_pipeline.py
- [ ] T114 [P] [US3] Write integration test test_issue_183_memory_bounded in tests/integration/test_full_pipeline.py (insert 10,000 entries, verify ≤1000 cached)
- [ ] T115 [P] [US3] Write performance test test_aggregation_cache_hit_performance in tests/performance/test_performance.py (verify P50 <5ms)
- [ ] T116 [P] [US3] Write performance test test_aggregation_cache_miss_performance in tests/performance/test_performance.py (verify P50 <30ms)

### Implementation for User Story 3

- [ ] T117 [US3] Implement aggregate_and_rank() main function in search/aggregation_module.py
- [ ] T118 [US3] Implement _calculate_relevance_score() helper in search/aggregation_module.py (hybrid_v3: text 40% + quality 30% + popularity 30%)
- [ ] T119 [US3] Implement _rank_recipes() helper in search/aggregation_module.py (score descending, name tie-break)
- [ ] T120 [US3] Implement _generate_cache_key() helper in search/aggregation_module.py (include all filters except pagination)
- [ ] T121 [US3] Implement LRU cache with functools.lru_cache(maxsize=1000) in search/aggregation_module.py
- [ ] T122 [US3] Implement cache TTL checking with timestamps in search/aggregation_module.py (TTL=300 seconds)
- [ ] T123 [US3] Implement _paginate_recipes() helper in search/aggregation_module.py (slice by page/page_size)
- [ ] T124 [US3] Implement _calculate_total_pages() helper in search/aggregation_module.py (ceil(total / page_size))
- [ ] T125 [US3] Add cache hit/miss tracking in search/aggregation_module.py
- [ ] T126 [US3] Add logging for ranking and cache operations in search/aggregation_module.py
- [ ] T127 [US3] Add performance timing measurement in search/aggregation_module.py (target P50 <5ms cache hit, <30ms cache miss)
- [ ] T128 [US3] Add total_duration_ms calculation (sum of all module durations) in search/aggregation_module.py
- [ ] T129 [US3] Remove dead ranking code from legacy search.py (ranking_v1, ranking_v2, failed A/B test algorithms)

### Verification for User Story 3

- [ ] T130 [US3] Run pytest tests/unit/test_aggregation_module.py --cov=search.aggregation_module (verify ≥80% coverage)
- [ ] T131 [US3] Run pytest tests/contract/test_aggregation_contract.py (verify all contracts pass)
- [ ] T132 [US3] Run pytest tests/integration/test_full_pipeline.py (verify full pipeline works)
- [ ] T133 [US3] Run pytest tests/performance/test_performance.py (verify P50 <5ms cache hit, <30ms cache miss)
- [ ] T134 [US3] Run mypy search/aggregation_module.py --strict (verify zero type errors)
- [ ] T135 [US3] Run pylint search/aggregation_module.py (verify score ≥9.0/10)
- [ ] T136 [US3] Verify module line count ≤300 lines (excluding comments/blank lines)
- [ ] T137 [US3] Run load test: 1000 concurrent searches for 1 hour, verify P95 ≤200ms and memory ≤50MB

**Checkpoint**: ✅ User Story 3 complete - Issue #183 FIXED, cache bounded, latency improved, performance targets met

**Acceptance Criteria**:
- ✅ SC-004: Average latency ≤100ms (P50)
- ✅ SC-005: P95 latency ≤200ms
- ✅ SC-006: Cache hit rate ≥60%
- ✅ SC-007: Cache memory ≤50MB bounded (Issue #183 fixed)
- ✅ SC-008: Aggregation module achieves ≥80% coverage
- ✅ SC-011: mypy strict passes, pylint ≥9.0/10
- ✅ SC-012: aggregation_module ≤300 lines

---

## Phase 6: User Story 4 - Clean, Modern Codebase (Priority: P4)

**Goal**: Eliminate all 74 magic numbers, remove deprecated code, complete type hints, pass static analysis

**Independent Test**: Run pylint and mypy on all modules, verify score ≥9.0/10 and zero type errors

**Why Fourth**: Technical debt cleanup makes future changes safer but system can function with debt. Pays dividends long-term.

### Tests for User Story 4 (Write FIRST)

- [ ] T138 [P] [US4] Write unit test test_format_recipe_converts_uuid_to_string in tests/unit/test_formatting_module.py
- [ ] T139 [P] [US4] Write unit test test_format_recipe_rounds_rating in tests/unit/test_formatting_module.py
- [ ] T140 [P] [US4] Write unit test test_format_recipe_preserves_all_fields in tests/unit/test_formatting_module.py
- [ ] T141 [P] [US4] Write unit test test_format_recipe_handles_empty_lists in tests/unit/test_formatting_module.py
- [ ] T142 [P] [US4] Write unit test test_format_response_populates_all_fields in tests/unit/test_formatting_module.py
- [ ] T143 [P] [US4] Write unit test test_format_response_empty_recipes in tests/unit/test_formatting_module.py
- [ ] T144 [P] [US4] Write unit test test_format_response_single_page in tests/unit/test_formatting_module.py
- [ ] T145 [P] [US4] Write unit test test_format_response_multiple_pages in tests/unit/test_formatting_module.py
- [ ] T146 [P] [US4] Write unit test test_format_response_cache_hit_preserved in tests/unit/test_formatting_module.py
- [ ] T147 [P] [US4] Write unit test test_format_response_duration_preserved in tests/unit/test_formatting_module.py
- [ ] T148 [P] [US4] Write unit test test_total_pages_calculation in tests/unit/test_formatting_module.py
- [ ] T149 [P] [US4] Write unit test test_json_serialization in tests/unit/test_formatting_module.py
- [ ] T150 [P] [US4] Write contract test test_contract_returns_search_response_type in tests/contract/test_formatting_contract.py
- [ ] T151 [P] [US4] Write contract test test_contract_recipes_list_never_none in tests/contract/test_formatting_contract.py
- [ ] T152 [P] [US4] Write contract test test_contract_all_fields_json_serializable in tests/contract/test_formatting_contract.py
- [ ] T153 [P] [US4] Write contract test test_contract_recipe_dicts_have_required_keys in tests/contract/test_formatting_contract.py
- [ ] T154 [P] [US4] Write contract test test_contract_total_pages_matches_calculation in tests/contract/test_formatting_contract.py
- [ ] T155 [P] [US4] Write contract test test_contract_pagination_metadata_consistent in tests/contract/test_formatting_contract.py
- [ ] T156 [P] [US4] Write integration test test_end_to_end_search_pipeline in tests/integration/test_full_pipeline.py
- [ ] T157 [P] [US4] Write integration test test_backward_compatibility_response_format in tests/integration/test_full_pipeline.py
- [ ] T158 [P] [US4] Write integration test test_api_endpoint_returns_json in tests/integration/test_full_pipeline.py
- [ ] T159 [P] [US4] Write performance test test_formatting_performance in tests/performance/test_performance.py (verify P50 <5ms)

### Implementation for User Story 4

- [ ] T160 [US4] Implement format_response() main function in search/formatting_module.py
- [ ] T161 [US4] Implement _format_recipe() helper in search/formatting_module.py (UUID→string, round rating to 1 decimal)
- [ ] T162 [US4] Implement _calculate_total_pages() helper in search/formatting_module.py (ceil(total / page_size))
- [ ] T163 [US4] Add logging for formatting operations in search/formatting_module.py
- [ ] T164 [US4] Add performance timing measurement in search/formatting_module.py (target P50 <5ms)
- [ ] T165 [US4] Remove legacy XML formatting code from old search.py (incomplete feature never used)
- [ ] T166 [US4] Verify all 74 magic numbers extracted to search/constants.py (grep for numeric literals)
- [ ] T167 [US4] Add complete type hints to all functions in all 4 modules (verify with mypy --strict)
- [ ] T168 [US4] Remove all deprecated code from legacy search.py (v1, v2 functions, commented-out blocks)
- [ ] T169 [US4] Externalize configuration to environment variables (DB credentials, feature flags, cache settings)

### Verification for User Story 4

- [ ] T170 [US4] Run pytest tests/unit/test_formatting_module.py --cov=search.formatting_module (verify ≥80% coverage)
- [ ] T171 [US4] Run pytest tests/contract/test_formatting_contract.py (verify all contracts pass)
- [ ] T172 [US4] Run pytest tests/integration/test_full_pipeline.py (verify complete pipeline works)
- [ ] T173 [US4] Run pytest tests/performance/test_performance.py (verify P50 <5ms)
- [ ] T174 [US4] Run mypy search/ --strict (verify zero type errors across ALL modules)
- [ ] T175 [US4] Run pylint search/ (verify score ≥9.0/10 across ALL modules)
- [ ] T176 [US4] Verify formatting_module line count ≤300 lines (excluding comments/blank lines)
- [ ] T177 [US4] Run grep -r '\b[0-9]\{2,\}\b' search/ to verify no magic numbers remain
- [ ] T178 [US4] Verify backward compatibility: Compare new vs legacy response format byte-by-byte

**Checkpoint**: ✅ User Story 4 complete - All technical debt eliminated, code clean and modern

**Acceptance Criteria**:
- ✅ SC-008: Formatting module achieves ≥80% coverage
- ✅ SC-009: All 74 magic numbers replaced with named constants
- ✅ SC-010: All deprecated code removed
- ✅ SC-011: mypy strict passes, pylint ≥9.0/10 (all modules)
- ✅ SC-012: formatting_module ≤300 lines
- ✅ SC-015: Zero breaking changes to public API

---

## Phase 7: Polish & Cross-Cutting Concerns (Final Integration)

**Purpose**: Complete integration, deployment preparation, documentation

- [ ] T179 Implement search_recipes() public API in search/__init__.py with backward-compatible signature
- [ ] T180 Add feature flag integration for gradual rollout (USE_NEW_VALIDATION, USE_NEW_FILTERING, USE_NEW_AGGREGATION, USE_NEW_FORMATTING)
- [ ] T181 Add automatic fallback to legacy search.py on exceptions in each module
- [ ] T182 Update main.py to import from search/ package instead of search.py
- [ ] T183 Add comprehensive docstrings to all public functions following Google style guide
- [ ] T184 [P] Update README.md with module architecture diagram and quickstart instructions
- [ ] T185 [P] Create MIGRATION.md guide for gradual rollout strategy (Week 1-4 plan)
- [ ] T186 Run full test suite: pytest --cov=search --cov-report=html (verify ≥80% coverage across entire package)
- [ ] T187 Run mypy search/ --strict (final verification zero type errors)
- [ ] T188 Run pylint search/ (final verification score ≥9.0/10)
- [ ] T189 Run load test: 1000 concurrent users for 1 hour (verify P50 ≤100ms, P95 ≤200ms, memory ≤50MB)
- [ ] T190 Create rollback plan documentation (how to disable feature flags and revert to legacy search.py)
- [ ] T191 Update CI/CD pipeline to run tests for search/ package
- [ ] T192 Create production deployment checklist (feature flags, monitoring, rollback procedure)

**Final Checkpoint**: ✅ All 4 user stories complete, all modules integrated, ready for production deployment

---

## Dependencies & Parallel Execution

### Dependency Graph

```
Phase 1 (Setup) → Phase 2 (Foundational)
                      ↓
        ┌────────────┼────────────┬────────────┐
        ↓            ↓            ↓            ↓
    Phase 3      Phase 4      Phase 5      Phase 6
    (US1)        (US2)        (US3)        (US4)
    [P1 MVP]     [P2]         [P3]         [P4]
        ↓            ↓            ↓            ↓
        └────────────┴────────────┴────────────┘
                      ↓
                  Phase 7 (Polish)
```

**Critical Path**: Phase 1 → Phase 2 → Phase 3 (US1) → Phase 7

**Parallel Opportunities**:
- After Phase 2 completes: Phases 3, 4, 5, 6 can run in parallel (different modules)
- Within each phase: All tasks marked [P] can run in parallel
- Tests within each phase: All test writing tasks [P] can run simultaneously

### Parallelization Examples

**After T011 (Foundation complete)**:
- Team A: Implement US1 (validation_module) - T012 to T045
- Team B: Implement US2 (filtering_module) - T046 to T087
- Team C: Implement US3 (aggregation_module) - T088 to T137
- Team D: Implement US4 (formatting_module) - T138 to T178

**Within US1 (after T030-T039 implementation)**:
- Run T012-T029 test writing tasks in parallel (15 unit tests + 3 contract tests)
- Run T040-T045 verification tasks in parallel (pytest, mypy, pylint, manual test)

**Within US2 (after T068-T080 implementation)**:
- Run T046-T067 test writing tasks in parallel (22 tests)
- Run T081-T087 verification tasks in parallel

**Within US3 (after T117-T129 implementation)**:
- Run T088-T116 test writing tasks in parallel (29 tests)
- Run T130-T137 verification tasks in parallel

**Within US4 (after T160-T169 implementation)**:
- Run T138-T159 test writing tasks in parallel (22 tests)
- Run T170-T178 verification tasks in parallel

---

## Implementation Strategy

### MVP First (Priority P1 Only)

**Minimum Viable Product**: User Story 1 (validation_module) only

**Rationale**: Fixes critical production bug affecting 30% of users. Delivers immediate value.

**MVP Scope**: T001-T045 (Phase 1 → Phase 2 → Phase 3)

**MVP Timeline**: 3-5 days
- Day 1: Setup + Foundational (T001-T011)
- Day 2-3: Write tests + Implement validation_module (T012-T039)
- Day 4: Verification + Integration (T040-T045)
- Day 5: Deploy to production with USE_NEW_VALIDATION=true

**Post-MVP**: Incrementally add US2, US3, US4 (can be deployed independently)

### Incremental Delivery

**Week 1**: MVP (US1) - Fix Issue #447
- Deploy: USE_NEW_VALIDATION=true
- Rollback: Set USE_NEW_VALIDATION=false

**Week 2**: Add US2 (filtering_module)
- Deploy: USE_NEW_FILTERING=true
- Rollback: Set USE_NEW_FILTERING=false

**Week 3**: Add US3 (aggregation_module) - Fix Issue #183
- Deploy: USE_NEW_AGGREGATION=true
- Rollback: Set USE_NEW_AGGREGATION=false

**Week 4**: Add US4 (formatting_module) + Polish
- Deploy: USE_NEW_FORMATTING=true
- Complete: All 4 modules live, deprecate legacy search.py

---

## Success Metrics (Final Verification)

After all tasks complete, verify:

✅ **SC-001**: Zero crashes for dietary_restrictions=None (manual test + monitoring)  
✅ **SC-002**: Zero production errors from search module (check error logs)  
✅ **SC-003**: All edge cases handled gracefully (run edge case test suite)  
✅ **SC-004**: Average latency ≤100ms P50 (load test results)  
✅ **SC-005**: P95 latency ≤200ms (load test results)  
✅ **SC-006**: Cache hit rate ≥60% (monitoring metrics)  
✅ **SC-007**: Cache memory ≤50MB bounded (memory profiling)  
✅ **SC-008**: All modules ≥80% coverage (pytest --cov results)  
✅ **SC-009**: Zero magic numbers (grep verification)  
✅ **SC-010**: All deprecated code removed (manual review)  
✅ **SC-011**: pylint ≥9.0/10, mypy strict passes (static analysis results)  
✅ **SC-012**: All modules ≤300 lines (line count verification)  
✅ **SC-013**: Module understandable in ≤15 minutes (developer survey)  
✅ **SC-014**: 100% API consumers working (backward compatibility tests)  
✅ **SC-015**: Zero breaking changes (integration test suite)  
✅ **SC-016**: Rollback capability within 5 minutes (rollback drill)

---

**Total Tasks**: 192 tasks  
**Estimated Effort**: 3-4 weeks with 4 developers (1 week per user story in parallel after foundation)

**Next Steps**: Begin with Phase 1 (Setup), complete Phase 2 (Foundational), then prioritize MVP (User Story 1) for immediate production deployment.
