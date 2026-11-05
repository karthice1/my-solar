#!/usr/bin/env python3
"""
Automated Test Suite for Exact TNEB Consumer Number Matching & Reliability
Covers all 10 required acceptance scenarios using mock data without requiring live TNEB login:
1. Exact consumer number match -> Continue extraction
2. No matching consumer number -> Stop with Consumer Number Not Found
3. Partial number match -> Reject
4. Prefix match -> Reject
5. Suffix match -> Reject
6. Multiple similar consumer numbers -> Select only exact match
7. Empty consumer number -> Reject safely
8. Ledger consumer number mismatch -> Stop extraction
9. Matching consumer and ledger numbers -> Continue extraction
10. No available connections -> Show genuine error
"""

import os
import sys
import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tneb_tool import (
    normalize_consumer_number,
    is_exact_consumer_match,
    find_matching_consumer_connection,
    extract_ledger_consumer_number,
    extract_account_summary_and_details,
    init_connection_state,
    scan_registered_connections,
    safe_cleanup_consumer_number
)

class TestExactConsumerNumberMatching(unittest.TestCase):
    
    def setUp(self):
        self.mock_connections = [
            {"index": 0, "consumerNo": "04406007211", "consumerName": "ANON USER SHORT"},
            {"index": 1, "consumerNo": "044060072111", "consumerName": "R.VASANTHAKUMAR"},
            {"index": 2, "consumerNo": "0440600721110", "consumerName": "ANON USER LONG"},
            {"index": 3, "consumerNo": "04406007627", "consumerName": "ANON USER SAMPLE2"},
            {"index": 4, "consumerNo": "04-406-005-994", "consumerName": "ANON USER FORMATTED"}
        ]

    def _create_mock_page(self, connections, num_pages=1):
        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        
        mock_locator = MagicMock()
        mock_locator.count = AsyncMock(return_value=num_pages)
        
        mock_btn = MagicMock()
        mock_btn.click = AsyncMock()
        mock_locator.nth = MagicMock(return_value=mock_btn)
        mock_locator.first = mock_btn
        
        mock_page.locator = MagicMock(return_value=mock_locator)
        mock_page.evaluate = AsyncMock(return_value=connections)
        return mock_page

    def _create_mock_context(self, mock_det_page):
        async def _get_val():
            return mock_det_page
        mock_info = MagicMock()
        mock_info.value = _get_val()
        
        mock_expect = MagicMock()
        mock_expect.__aenter__ = AsyncMock(return_value=mock_info)
        mock_expect.__aexit__ = AsyncMock(return_value=None)
        
        mock_context = MagicMock()
        mock_context.expect_page = MagicMock(return_value=mock_expect)
        return mock_context

    # Scenario 1: Exact consumer number match -> Continue extraction
    def test_01_exact_consumer_match(self):
        target = "044060072111"
        candidate = "044060072111"
        self.assertTrue(is_exact_consumer_match(target, candidate))
        
        # Test with formatting (hyphens, spaces)
        self.assertTrue(is_exact_consumer_match("04-406-007-2111", "044060072111"))
        self.assertTrue(is_exact_consumer_match(" 04 406 007 2111 ", "044060072111"))
        
        matched = find_matching_consumer_connection(self.mock_connections, target)
        self.assertIsNotNone(matched)
        self.assertEqual(matched["index"], 1)
        self.assertEqual(matched["consumerNo"], "044060072111")
        self.assertEqual(matched["consumerName"], "R.VASANTHAKUMAR")

    # Scenario 2: No matching consumer number -> Stop with Consumer Number Not Found
    def test_02_no_matching_consumer_number(self):
        target = "044069999999" # Not in mock connections
        matched = find_matching_consumer_connection(self.mock_connections, target)
        self.assertIsNone(matched)
        
        # Async test of extract_account_summary_and_details when not found
        async def run_not_found():
            mock_context = MagicMock()
            mock_page = self._create_mock_page(self.mock_connections, num_pages=1)
            result = await extract_account_summary_and_details(mock_context, mock_page, target)
            return result
            
        result = asyncio.run(run_not_found())
        self.assertIn("error", result)
        self.assertEqual(result["title"], "Consumer Number Not Found")
        expected_msg = (
            "The consumer number you entered could not be found in your TNEB account. "
            "Please verify the consumer number and try again. No billing information has been extracted."
        )
        self.assertEqual(result["error"], expected_msg)

    # Scenario 3: Partial number match -> Reject
    def test_03_partial_match_rejected(self):
        target = "04406"
        candidate = "044060072111"
        self.assertFalse(is_exact_consumer_match(target, candidate))
        self.assertFalse(is_exact_consumer_match(candidate, target))
        
        matched = find_matching_consumer_connection(self.mock_connections, target)
        self.assertIsNone(matched)

    # Scenario 4: Prefix match -> Reject
    def test_04_prefix_match_rejected(self):
        # Target is missing last digit
        target = "04406007211"
        # Candidate has extra digit
        candidate = "044060072111"
        self.assertFalse(is_exact_consumer_match(target, candidate))
        
        # When searching for target "04406007211", it must match row 0 ("04406007211"), not row 1 ("044060072111")
        matched = find_matching_consumer_connection(self.mock_connections, target)
        self.assertIsNotNone(matched)
        self.assertEqual(matched["index"], 0)
        self.assertEqual(matched["consumerNo"], "04406007211")

    # Scenario 5: Suffix match -> Reject
    def test_05_suffix_match_rejected(self):
        # Target without region code "04"
        target = "4060072111"
        candidate = "044060072111"
        self.assertFalse(is_exact_consumer_match(target, candidate))
        self.assertFalse(is_exact_consumer_match(candidate, target))
        
        matched = find_matching_consumer_connection(self.mock_connections, target)
        self.assertIsNone(matched)

    # Scenario 6: Multiple similar consumer numbers -> Select only exact match
    def test_06_multiple_similar_numbers_selects_only_exact(self):
        similar_connections = [
            {"index": 0, "consumerNo": "04406007211"},
            {"index": 1, "consumerNo": "044060072111"},
            {"index": 2, "consumerNo": "0440600721110"},
            {"index": 3, "consumerNo": "0440600721"}
        ]
        target = "044060072111"
        matched = find_matching_consumer_connection(similar_connections, target)
        self.assertIsNotNone(matched)
        self.assertEqual(matched["index"], 1)
        self.assertEqual(matched["consumerNo"], "044060072111")

    # Scenario 7: Empty consumer number -> Reject safely
    def test_07_empty_consumer_number_rejected_safely(self):
        self.assertEqual(normalize_consumer_number(""), "")
        self.assertEqual(normalize_consumer_number(None), "")
        self.assertEqual(normalize_consumer_number("   "), "")
        self.assertEqual(normalize_consumer_number("---"), "")
        self.assertEqual(normalize_consumer_number("abc-xyz"), "")
        
        self.assertFalse(is_exact_consumer_match("", "044060072111"))
        self.assertFalse(is_exact_consumer_match(None, "044060072111"))
        self.assertFalse(is_exact_consumer_match("044060072111", ""))
        self.assertFalse(is_exact_consumer_match("", ""))
        
        matched = find_matching_consumer_connection(self.mock_connections, "")
        self.assertIsNone(matched)
        
        # In extract_account_summary_and_details
        async def run_empty():
            mock_context = MagicMock()
            mock_page = self._create_mock_page(self.mock_connections, num_pages=1)
            return await extract_account_summary_and_details(mock_context, mock_page, "")
            
        result = asyncio.run(run_empty())
        self.assertIn("error", result)
        self.assertEqual(result["title"], "Consumer Number Not Found")

    # Scenario 8: Ledger consumer number mismatch -> Stop extraction
    def test_08_ledger_consumer_number_mismatch_stops_extraction(self):
        target = "044060072111"
        mismatched_ledger_html = """
        <html><body>
        <table>
        <tr>
            <td>CONSUMER NAME: OTHER PERSON</td>
            <td>CONSUMER NUMBER: 044060079999</td>
        </tr>
        </table>
        </body></html>
        """
        ledger_no = extract_ledger_consumer_number(mismatched_ledger_html, "CONSUMER NUMBER: 044060079999")
        self.assertEqual(ledger_no, "044060079999")
        self.assertFalse(is_exact_consumer_match(target, ledger_no))
        
        # Test full extract_account_summary_and_details handling of mismatch
        async def run_mismatch():
            # Mock clicking detconws form button
            mock_det_page = MagicMock()
            mock_det_page.wait_for_load_state = AsyncMock()
            mock_det_page.content = AsyncMock(return_value=mismatched_ledger_html)
            mock_det_page.inner_text = AsyncMock(return_value="CONSUMER NUMBER: 044060079999")
            mock_det_page.close = AsyncMock()
            
            mock_context = self._create_mock_context(mock_det_page)
            mock_page = self._create_mock_page(self.mock_connections, num_pages=1)
            
            return await extract_account_summary_and_details(mock_context, mock_page, target)
            
        result = asyncio.run(run_mismatch())
        self.assertIn("error", result)
        self.assertEqual(result["title"], "Consumer Verification Failed")
        expected_msg = (
            "Consumer verification failed. The account details retrieved from TNEB do not match "
            "the requested consumer number. Extraction has been stopped for your protection."
        )
        self.assertEqual(result["error"], expected_msg)

    # Scenario 9: Matching consumer and ledger numbers -> Continue extraction
    def test_09_matching_consumer_and_ledger_numbers_continues(self):
        target = "044060072111"
        valid_ledger_html = """
        <html><body>
        <table>
        <tr>
            <td>CONSUMER NAME: R.VASANTHAKUMAR</td>
            <td>CONSUMER NUMBER: 044060072111</td>
        </tr>
        <tr><td>SANCTIONED LOAD</td><td>5.0 KW</td></tr>
        <tr><td>TARIFF CODE</td><td>LA1A</td></tr>
        <tr><td>SERVICE STATUS</td><td>LIVE</td></tr>
        <tr><td>27/10/2026</td><td>27/10/2026</td><td>NORMAL</td><td>38779</td><td>0</td><td>1.99</td><td>0</td><td>392</td><td>902.4</td></tr>
        </table>
        </body></html>
        """
        ledger_no = extract_ledger_consumer_number(valid_ledger_html, "CONSUMER NUMBER: 044060072111")
        self.assertEqual(ledger_no, "044060072111")
        self.assertTrue(is_exact_consumer_match(target, ledger_no))
        
        async def run_valid():
            mock_det_page = MagicMock()
            mock_det_page.wait_for_load_state = AsyncMock()
            mock_det_page.content = AsyncMock(return_value=valid_ledger_html)
            mock_det_page.inner_text = AsyncMock(return_value="CONSUMER NUMBER: 044060072111")
            mock_det_page.screenshot = AsyncMock()
            mock_det_page.close = AsyncMock()
            
            mock_context = self._create_mock_context(mock_det_page)
            mock_page = self._create_mock_page(self.mock_connections, num_pages=1)
            
            with patch("tneb_tool.parse_detconws_page") as mock_parse:
                mock_parse.return_value = {
                    "consumer_no": "044060072111",
                    "consumer_name": "R.VASANTHAKUMAR",
                    "billing_cycles": [{"units_consumed": 392.0}]
                }
                return await extract_account_summary_and_details(mock_context, mock_page, target)
                
        result = asyncio.run(run_valid())
        self.assertNotIn("error", result)
        self.assertEqual(result["consumer_no"], "044060072111")
        self.assertEqual(len(result["billing_cycles"]), 1)

    # Scenario 10: No available connections -> Show genuine error
    def test_10_no_available_connections_shows_genuine_error(self):
        target = "044060072111"
        matched = find_matching_consumer_connection([], target)
        self.assertIsNone(matched)
        
        async def run_empty_table():
            mock_context = MagicMock()
            mock_page = self._create_mock_page([], num_pages=0) # 0 pages
            
            return await extract_account_summary_and_details(mock_context, mock_page, target)
            
        result = asyncio.run(run_empty_table())
        self.assertIn("error", result)
        self.assertEqual(result["title"], "Consumer Number Not Found")
        expected_msg = (
            "The consumer number you entered could not be found in your TNEB account. "
            "Please verify the consumer number and try again. No billing information has been extracted."
        )
        self.assertEqual(result["error"], expected_msg)


class TestCleanupProtectionRegression(unittest.TestCase):
    """
    Automated Regression Test Suite for TNEB Primary & Pre-existing Consumer Account Protection.
    Verifies that the extractor NEVER deletes, modifies, or disturbs primary or pre-existing connections.
    Covers all 12 regression scenarios required by specification:
    1. Primary consumer extraction -> Extract successfully, never delete (RETAINED_PRIMARY)
    2. Existing secondary consumer -> Extract successfully, retain connection (RETAINED_PREEXISTING)
    3. Newly added temporary connection -> Extract and delete exact temporary connection (SUCCESS_REMOVED)
    4. Temporary connection extraction failure -> Attempt safe cleanup only
    5. Primary consumer with extraction failure -> Never delete primary connection
    6. Secondary pre-existing connection with extraction failure -> Never delete it
    7. Multiple registered connections -> Delete only the newly added temporary connection
    8. Similar consumer numbers -> Never delete a partial or similar match
    9. Deletion target mismatch -> Abort deletion (SAFETY_PREVENTED)
    10. Deletion verification failure -> Report cleanup as unverified (FAILED_VERIFICATION)
    11. Unknown connection status -> Do not delete (SAFETY_PREVENTED)
    12. No deletion form available -> Stop cleanup safely (SAFETY_PREVENTED)
    13. Reliable portal evidence -> Identify primary connection by missing delete button regardless of row order
    """

    def _create_cleanup_mock_page(self, eval_responses, button_mocks=None):
        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        
        mock_locator = MagicMock()
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.is_visible = AsyncMock(return_value=False)
        mock_locator.first = mock_locator
        
        def _get_locator(selector):
            if button_mocks and selector in button_mocks:
                return button_mocks[selector]
            return mock_locator
            
        mock_page.locator = MagicMock(side_effect=_get_locator)
        
        if isinstance(eval_responses, list):
            mock_page.evaluate = AsyncMock(side_effect=eval_responses)
        else:
            mock_page.evaluate = AsyncMock(return_value=eval_responses)
            
        return mock_page

    # Scenario 1: Primary consumer extraction -> Extract successfully, never delete
    def test_cleanup_01_primary_consumer_extraction_never_deleted(self):
        target = "044060072111"
        state = init_connection_state(target)
        state["is_primary_connection"] = True
        state["was_registered_before_extraction"] = True
        state["added_by_current_extraction"] = False
        
        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        
        result = asyncio.run(safe_cleanup_consumer_number(mock_page, state))
        self.assertFalse(result["cleanup_attempted"])
        self.assertFalse(result["cleanup_completed"])
        self.assertEqual(result["cleanup_status"], "RETAINED_PRIMARY")
        self.assertEqual(
            result["cleanup_message"],
            "Primary consumer connection detected. Your original TNEB connection has been retained."
        )
        mock_page.goto.assert_not_called()

    # Scenario 2: Existing secondary consumer -> Extract successfully, retain connection
    def test_cleanup_02_existing_secondary_consumer_retained(self):
        target = "044060072113"
        state = init_connection_state(target)
        state["is_primary_connection"] = False
        state["was_registered_before_extraction"] = True
        state["added_by_current_extraction"] = False
        
        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        
        result = asyncio.run(safe_cleanup_consumer_number(mock_page, state))
        self.assertFalse(result["cleanup_attempted"])
        self.assertFalse(result["cleanup_completed"])
        self.assertEqual(result["cleanup_status"], "RETAINED_PREEXISTING")
        self.assertEqual(
            result["cleanup_message"],
            "This consumer connection was already registered before extraction. It has been retained."
        )
        mock_page.goto.assert_not_called()

    # Scenario 3: Newly added temporary connection -> Extract and delete exact temporary connection
    def test_cleanup_03_newly_added_temporary_connection_deleted_and_verified(self):
        target = "04406007699"
        state = init_connection_state(target)
        state["is_primary_connection"] = False
        state["was_registered_before_extraction"] = False
        state["added_by_current_extraction"] = True
        
        mock_btn = MagicMock()
        mock_btn.click = AsyncMock()
        
        initial_eval = {
            "available": True,
            "rows": [
                {"index": 0, "consumerNo": "04406007699", "consumerName": "TEMP USER", "hasButton": True, "buttonId": "del_btn_temp"}
            ]
        }
        post_eval = ["044060072111"] # Target 04406007699 is no longer present!
        
        mock_page = self._create_cleanup_mock_page(
            eval_responses=[initial_eval, post_eval],
            button_mocks={"[id='del_btn_temp']": mock_btn}
        )
        
        result = asyncio.run(safe_cleanup_consumer_number(mock_page, state))
        self.assertTrue(result["cleanup_attempted"])
        self.assertTrue(result["cleanup_completed"])
        self.assertEqual(result["cleanup_status"], "SUCCESS_REMOVED")
        self.assertEqual(
            result["cleanup_message"],
            "Temporary consumer connection successfully removed after extraction."
        )
        mock_btn.click.assert_called_once()

    # Scenario 4: Temporary connection extraction failure -> Attempt safe cleanup only
    def test_cleanup_04_temporary_connection_extraction_failure_attempts_safe_cleanup(self):
        target = "04406007699"
        state = init_connection_state(target)
        state["is_primary_connection"] = False
        state["was_registered_before_extraction"] = False
        state["added_by_current_extraction"] = True
        state["extraction_completed"] = False # Simulated extraction error
        
        mock_btn = MagicMock()
        mock_btn.click = AsyncMock()
        
        initial_eval = {
            "available": True,
            "rows": [
                {"index": 0, "consumerNo": "04406007699", "consumerName": "TEMP USER", "hasButton": True, "buttonId": "del_btn_temp"}
            ]
        }
        post_eval = []
        
        mock_page = self._create_cleanup_mock_page(
            eval_responses=[initial_eval, post_eval],
            button_mocks={"[id='del_btn_temp']": mock_btn}
        )
        
        result = asyncio.run(safe_cleanup_consumer_number(mock_page, state))
        self.assertTrue(result["cleanup_attempted"])
        self.assertTrue(result["cleanup_completed"])
        self.assertEqual(result["cleanup_status"], "SUCCESS_REMOVED")
        mock_btn.click.assert_called_once()

    # Scenario 5: Primary consumer with extraction failure -> Never delete primary connection
    def test_cleanup_05_primary_consumer_extraction_failure_never_deleted(self):
        target = "044060072111"
        state = init_connection_state(target)
        state["is_primary_connection"] = True
        state["was_registered_before_extraction"] = True
        state["added_by_current_extraction"] = False
        state["extraction_completed"] = False
        
        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        
        result = asyncio.run(safe_cleanup_consumer_number(mock_page, state))
        self.assertFalse(result["cleanup_attempted"])
        self.assertFalse(result["cleanup_completed"])
        self.assertEqual(result["cleanup_status"], "RETAINED_PRIMARY")
        mock_page.goto.assert_not_called()

    # Scenario 6: Secondary pre-existing connection with extraction failure -> Never delete it
    def test_cleanup_06_secondary_preexisting_extraction_failure_never_deleted(self):
        target = "044060072113"
        state = init_connection_state(target)
        state["is_primary_connection"] = False
        state["was_registered_before_extraction"] = True
        state["added_by_current_extraction"] = False
        state["extraction_completed"] = False
        
        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        
        result = asyncio.run(safe_cleanup_consumer_number(mock_page, state))
        self.assertFalse(result["cleanup_attempted"])
        self.assertFalse(result["cleanup_completed"])
        self.assertEqual(result["cleanup_status"], "RETAINED_PREEXISTING")
        mock_page.goto.assert_not_called()

    # Scenario 7: Multiple registered connections -> Delete only the newly added temporary connection
    def test_cleanup_07_multiple_registered_connections_deletes_only_temporary(self):
        target = "04406007699"
        state = init_connection_state(target)
        state["added_by_current_extraction"] = True
        
        mock_preexisting_btn = MagicMock()
        mock_preexisting_btn.click = AsyncMock()
        mock_temp_btn = MagicMock()
        mock_temp_btn.click = AsyncMock()
        
        initial_eval = {
            "available": True,
            "rows": [
                {"index": 0, "consumerNo": "044060072111", "consumerName": "PRIMARY USER", "hasButton": False, "buttonId": ""},
                {"index": 1, "consumerNo": "044060072113", "consumerName": "PREEXISTING USER", "hasButton": True, "buttonId": "del_btn_pre"},
                {"index": 2, "consumerNo": "04406007699", "consumerName": "TEMP USER", "hasButton": True, "buttonId": "del_btn_temp"}
            ]
        }
        post_eval = ["044060072111", "044060072113"] # Both primary and preexisting remain untouched!
        
        mock_page = self._create_cleanup_mock_page(
            eval_responses=[initial_eval, post_eval],
            button_mocks={
                "[id='del_btn_pre']": mock_preexisting_btn,
                "[id='del_btn_temp']": mock_temp_btn
            }
        )
        
        result = asyncio.run(safe_cleanup_consumer_number(mock_page, state))
        self.assertTrue(result["cleanup_completed"])
        self.assertEqual(result["cleanup_status"], "SUCCESS_REMOVED")
        mock_temp_btn.click.assert_called_once()
        mock_preexisting_btn.click.assert_not_called()

    # Scenario 8: Similar consumer numbers -> Never delete a partial or similar match
    def test_cleanup_08_similar_consumer_numbers_never_deleted(self):
        target = "04406007699"
        state = init_connection_state(target)
        state["added_by_current_extraction"] = True
        
        mock_btn_short = MagicMock()
        mock_btn_short.click = AsyncMock()
        mock_btn_long = MagicMock()
        mock_btn_long.click = AsyncMock()
        
        initial_eval = {
            "available": True,
            "rows": [
                {"index": 0, "consumerNo": "0440600769", "consumerName": "SHORT SIMILAR", "hasButton": True, "buttonId": "del_btn_short"},
                {"index": 1, "consumerNo": "044060076990", "consumerName": "LONG SIMILAR", "hasButton": True, "buttonId": "del_btn_long"}
            ]
        }
        
        mock_page = self._create_cleanup_mock_page(
            eval_responses=[initial_eval],
            button_mocks={
                "[id='del_btn_short']": mock_btn_short,
                "[id='del_btn_long']": mock_btn_long
            }
        )
        
        result = asyncio.run(safe_cleanup_consumer_number(mock_page, state))
        # Neither similar button is ever clicked!
        mock_btn_short.click.assert_not_called()
        mock_btn_long.click.assert_not_called()

    # Scenario 9: Deletion target mismatch -> Abort deletion
    def test_cleanup_09_deletion_target_mismatch_aborts_deletion(self):
        target = "04406007699"
        state = init_connection_state(target)
        state["added_by_current_extraction"] = True
        
        mock_btn = MagicMock()
        mock_btn.click = AsyncMock()
        
        initial_eval = {
            "available": True,
            "rows": [
                {"index": 0, "consumerNo": "04406007888", "consumerName": "MISMATCHED USER", "hasButton": True, "buttonId": "del_btn_mismatch"}
            ]
        }
        
        mock_page = self._create_cleanup_mock_page(
            eval_responses=[initial_eval],
            button_mocks={"[id='del_btn_mismatch']": mock_btn}
        )
        
        result = asyncio.run(safe_cleanup_consumer_number(mock_page, state))
        mock_btn.click.assert_not_called()

    # Scenario 10: Deletion verification failure -> Report cleanup as unverified
    def test_cleanup_10_deletion_verification_failure_reports_unverified(self):
        target = "04406007699"
        state = init_connection_state(target)
        state["added_by_current_extraction"] = True
        
        mock_btn = MagicMock()
        mock_btn.click = AsyncMock()
        
        initial_eval = {
            "available": True,
            "rows": [
                {"index": 0, "consumerNo": "04406007699", "consumerName": "TEMP USER", "hasButton": True, "buttonId": "del_btn_temp"}
            ]
        }
        # Post-deletion audit still finds target consumer number!
        post_eval = ["04406007699"]
        
        mock_page = self._create_cleanup_mock_page(
            eval_responses=[initial_eval, post_eval],
            button_mocks={"[id='del_btn_temp']": mock_btn}
        )
        
        result = asyncio.run(safe_cleanup_consumer_number(mock_page, state))
        self.assertTrue(result["cleanup_attempted"])
        self.assertFalse(result["cleanup_completed"])
        self.assertEqual(result["cleanup_status"], "FAILED_VERIFICATION")
        self.assertEqual(
            result["cleanup_message"],
            "Billing extraction completed, but automatic cleanup could not be verified. Please check your TNEB account manually."
        )

    # Scenario 11: Unknown connection status -> Do not delete
    def test_cleanup_11_unknown_connection_status_does_not_delete(self):
        target = "04406007699"
        state = init_connection_state(target)
        # Ambiguous identity / unknown origin:
        state["was_registered_before_extraction"] = False
        state["added_by_current_extraction"] = False
        state["is_primary_connection"] = False
        
        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        
        result = asyncio.run(safe_cleanup_consumer_number(mock_page, state))
        self.assertFalse(result["cleanup_attempted"])
        self.assertFalse(result["cleanup_completed"])
        self.assertEqual(result["cleanup_status"], "SAFETY_PREVENTED")
        self.assertEqual(
            result["cleanup_message"],
            "Automatic deletion was prevented because the connection's original registration status could not be verified. No deletion was attempted."
        )
        mock_page.goto.assert_not_called()

    # Scenario 12: No deletion form available -> Stop cleanup safely
    def test_cleanup_12_no_deletion_form_available_stops_safely(self):
        target = "04406007699"
        state = init_connection_state(target)
        state["added_by_current_extraction"] = True
        
        initial_eval = {
            "available": False,
            "rows": []
        }
        
        mock_page = self._create_cleanup_mock_page(eval_responses=[initial_eval])
        
        result = asyncio.run(safe_cleanup_consumer_number(mock_page, state))
        self.assertTrue(result["cleanup_attempted"])
        self.assertFalse(result["cleanup_completed"])
        self.assertEqual(result["cleanup_status"], "SAFETY_PREVENTED")
        self.assertEqual(
            result["cleanup_message"],
            "Automatic deletion was prevented because the connection's original registration status could not be verified. No deletion was attempted."
        )

    # Scenario 13: Reliable portal evidence determines primary status (missing delete button, not row order)
    def test_cleanup_13_scan_registered_connections_identifies_primary_by_portal_evidence(self):
        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        mock_locator = MagicMock()
        mock_locator.count = AsyncMock(return_value=1)
        mock_page.locator = MagicMock(return_value=mock_locator)
        
        # Primary is at row 1 (NOT row 0!), identified purely by hasButton == False
        mock_page.evaluate = AsyncMock(return_value=[
            {"consumerNo": "044060072113", "consumerName": "SECONDARY 1", "hasButton": True},
            {"consumerNo": "044060072111", "consumerName": "PRIMARY ACCOUNT", "hasButton": False},
            {"consumerNo": "04406007627", "consumerName": "SECONDARY 2", "hasButton": True}
        ])
        
        reg_map = asyncio.run(scan_registered_connections(mock_page))
        self.assertEqual(len(reg_map), 3)
        self.assertTrue(reg_map["044060072111"]["is_primary"])
        self.assertFalse(reg_map["044060072111"]["has_delete_btn"])
        
        self.assertFalse(reg_map["044060072113"]["is_primary"])
        self.assertTrue(reg_map["044060072113"]["has_delete_btn"])
        
        self.assertFalse(reg_map["04406007627"]["is_primary"])
        self.assertTrue(reg_map["04406007627"]["has_delete_btn"])


if __name__ == "__main__":
    unittest.main()
