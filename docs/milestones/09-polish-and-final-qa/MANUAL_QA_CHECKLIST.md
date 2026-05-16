# Manual QA Checklist - Milestone 9

## Pre-Testing Setup

```bash
# Ensure environment is ready
make venv
make install-dev
make qa

# Start the app
make run

# Access at http://localhost:8501
```

## Test Cases

### Test 1: Bundled Demo Repo Analysis

**Steps:**
1. Open app at http://localhost:8501
2. Sidebar should show "Use demo repo" selected by default
3. Click "Generate Quest" button
4. Wait for analysis to complete

**Expected Results:**
- No errors during analysis
- Input sidebar is hidden after analysis completes
- A simple Refresh action is available in the analysis workspace
- Overview tab shows "Full-stack web application"
- Confidence score >= 70%
- React + Vite detected in frameworks
- FastAPI detected in frameworks
- Entry points include backend/main.py and frontend/src/App.tsx
- Key folders include frontend/, backend/, components/, routes/

**Status:** Pending

---

### Test 2: Small Valid ZIP Upload

**Steps:**
1. Create a small test ZIP (< 5MB) with a simple Python project
2. Select "Upload ZIP" in sidebar
3. Upload the ZIP file
4. Click "Generate Quest"

**Expected Results:**
- Upload succeeds
- Analysis completes without errors
- Project type is detected (or "Unknown/mixed repo" if minimal)
- Files are listed in overview

**Status:** Pending

---

### Test 3: Invalid ZIP Handling

**Steps:**
1. Create a corrupted/invalid ZIP file
2. Select "Upload ZIP" in sidebar
3. Upload the invalid file
4. Click "Generate Quest"

**Expected Results:**
- Friendly error message appears
- No Python traceback shown in main UI
- App remains functional
- Can switch back to demo repo

**Status:** Pending

---

### Test 4: Oversized ZIP Rejection

**Steps:**
1. Create or obtain a ZIP file > 25MB
2. Select "Upload ZIP" in sidebar
3. Attempt to upload the file

**Expected Results:**
- Upload is rejected with size limit message
- Error message mentions "25 MB limit"
- App remains functional

**Status:** Pending

---

### Test 5: Empty/Minimal Repo

**Steps:**
1. Create a ZIP with only a README.md file
2. Upload and analyze

**Expected Results:**
- Analysis completes
- Project type: "Unknown/mixed repo"
- Confidence score is low (< 50%)
- Warning message about low confidence
- Reading path still generated (README first)

**Status:** Pending

---

### Test 6: Generate Quest Twice

**Steps:**
1. Analyze demo repo
2. Wait for completion
3. Click "Generate Quest" again
4. Verify state is reset and re-analyzed

**Expected Results:**
- Previous state is cleared
- New analysis runs successfully
- Results are consistent with first run
- No stale data from previous analysis

**Status:** Pending

---

### Test 7: Switch Between Sources

**Steps:**
1. Analyze demo repo
2. Switch to "Upload ZIP"
3. Upload a different repo
4. Analyze
5. Switch back to "Use demo repo"
6. Analyze again

**Expected Results:**
- Each analysis is independent
- No data leakage between sources
- State resets properly on each switch
- No errors during transitions

**Status:** Pending

---

### Test 8: Documentation Generation

**Steps:**
1. Analyze demo repo
2. Navigate to "Documentation" tab
3. Click "Generate Documentation" button
4. Wait for generation

**Expected Results:**
- Success message appears
- Preview shows generated content
- Preview is truncated with "..." indicator
- Full content available in Export tab

**Status:** Pending

---

### Test 9: Tests Tab with Tests

**Steps:**
1. Analyze demo repo (has backend/tests/test_trips.py)
2. Navigate to "Tests" tab

**Expected Results:**
- Shows "Found 1 test files"
- backend/tests/test_trips.py is listed
- Detects pytest framework
- Shows imports from test file
- Shows suggested next tests
- Test files NOT in dependency graph (Architecture Map tab)

**Status:** Pending

---

### Test 9A: Architecture Graph Polish

**Steps:**
1. Analyze demo repo
2. Navigate to "Architecture Map" tab
3. Verify application mode
4. Switch to tests mode

**Expected Results:**
- Graph renders horizontally
- Graph shows connected nodes only
- Legend is embedded in the graph with short labels
- No "Backend route/service" overflow label appears
- Purple Tests legend row appears in tests mode
- Dashed API boundary legend appears only when dashed API edge is present
- Inspector does not include a code preview

**Status:** Pending

---

### Test 10: Tests Tab Without Tests

**Steps:**
1. Upload a ZIP without test files
2. Analyze
3. Navigate to "Tests"tab

**Expected Results:**
- Shows "No test files detected"
- Friendly message about adding tests
- Suggests test ideas for API endpoints, business logic, etc.
- No errors or empty state issues

**Status:** Pending

---

### Test 11: Documentation Preview with README

**Steps:**
1. Analyze demo repo (has README.md)
2. Navigate to "Documentation"tab

**Expected Results:**
- README preview section appears
- Shows first ~1000 chars of README
- Truncation indicator if README is long
- Documentation files table shows README.md

**Status:** Pending

---

### Test 12: Documentation Preview Without README

**Steps:**
1. Upload a ZIP without README.md
2. Analyze
3. Navigate to "Documentation"tab

**Expected Results:**
- Shows "No README.md found"
- Friendly info message
- Documentation files table shows other docs (if any)
- Can still generate onboarding guide

**Status:** Pending

---

## Additional Verification Tests

### Test 13: Architecture Map Rendering

**Steps:**
1. Analyze demo repo
2. Navigate to "Architecture Map"tab

**Expected Results:**
- Human-friendly architecture graph renders
- Shows layers: Frontend -> Backend -> Services -> Models
- Dependency graph renders below
- Legend explains node colors and edge styles
- Routes table shows detected API endpoints

**Status:** Pending

---

### Test 14: Reading Path Generation

**Steps:**
1. Analyze demo repo
2. Navigate to "Reading Path"tab

**Expected Results:**
- Shows ~9 files in order
- README.md is first (if present)
- Backend entry point (main.py) early in path
- Each item has reason and estimated minutes
- Total time shown (~30 minutes)

**Status:** Pending

---

### Test 15: Component Cards

**Steps:**
1. Analyze demo repo
2. Navigate to "Components"tab

**Expected Results:**
- Shows multiple component cards
- Can filter by role
- Each card shows: role, why it matters, detected items, connections
- Code snippets appear for routes
- Suggested test ideas listed
- AI Assistant action provided

**Status:** Pending

---

### Test 16: Quiz Functionality

**Steps:**
1. Analyze demo repo
2. Navigate to "Quest & Quiz"tab
3. Answer quiz questions
4. Click "Submit Quiz"

**Expected Results:**
- Multiple quiz questions appear
- Can select answers
- Submit button works
- Correct/incorrect feedback shown
- Score calculated and displayed
- Can reset quiz

**Status:** Pending

---

### Test 17: Markdown Export

**Steps:**
1. Analyze demo repo
2. Navigate to "Export"tab
3. Review preview
4. Click "Download Onboarding Guide"

**Expected Results:**
- Full markdown preview shown
- Download button works
- Downloaded file is valid markdown
- Contains all sections: overview, frameworks, routes, reading path, components, quiz
- File name includes repo name

**Status:** Pending

---

### Test 18: Built with IBM Bob Section

**Steps:**
1. Navigate to "Built with IBM Bob"tab

**Expected Results:**
- Explains Bob's role in development
- Lists 8 development areas Bob helped with
- Clearly states "no AI at runtime"
- Explains deterministic analysis approach
- Mentions bob_sessions/ directory

**Status:** Pending

---

### Test 19: Reset Functionality

**Steps:**
1. Analyze demo repo
2. Click "Reset"button in sidebar

**Expected Results:**
- All tabs clear
- Welcome message reappears
- Can start fresh analysis
- No residual state

**Status:** Pending

---

### Test 20: Error Handling

**Steps:**
1. Try various edge cases:
  - ZIP with special characters in filenames
  - ZIP with very long paths
  - ZIP with binary files only
  - Rapid clicking of Generate button

**Expected Results:**
- Graceful error messages
- No Python tracebacks in main UI
- App remains functional after errors
- Can recover and continue

**Status:** Pending

---

## Performance Tests

### Test 21: Large Repo Handling

**Steps:**
1. Upload a ZIP with ~500 files
2. Analyze

**Expected Results:**
- Analysis completes within reasonable time (< 30 seconds)
- File limit warning if > 600 files
- Graph limited to 80 nodes
- No performance degradation in UI

**Status:** Pending

---

### Test 22: Graph Rendering Performance

**Steps:**
1. Analyze demo repo
2. Navigate between Architecture Map and other tabs multiple times

**Expected Results:**
- Graphs render quickly (< 2 seconds)
- No lag when switching tabs
- Graphs are readable and well-formatted

**Status:** Pending

---

## Security Tests

### Test 23: Path Traversal Protection

**Steps:**
1. Create a ZIP with paths like:
  - `../../../etc/passwd`
  - `/absolute/path/file.txt`
  - `dir/../../../escape.txt`
2. Attempt to upload and analyze

**Expected Results:**
- ZIP is rejected with security error
- Error message mentions "ZIP Safety Error"
- No files are extracted or executed
- App remains secure

**Status:** Pending

---

### Test 24: Binary File Handling

**Steps:**
1. Create a ZIP with binary files (.exe,.dll,.so,.pyc)
2. Upload and analyze

**Expected Results:**
- Binary files are skipped
- Skip reason shown in warnings
- No attempt to execute binaries
- Text files are still analyzed

**Status:** Pending

---

## Cross-Browser Tests (Optional)

### Test 25: Browser Compatibility

**Browsers to test:**
- Chrome/Chromium
- Firefox
- Safari (if available)
- Edge

**Expected Results:**
- UI renders correctly in all browsers
- File upload works
- Graphs render properly
- Download button works

**Status:** Pending

---

## Final Acceptance

### All Tests Passed

**Criteria:**
- [ ] All 25 manual tests completed
- [ ] No critical bugs found
- [ ] Performance is acceptable
- [ ] Security measures verified
- [ ] Demo flow practiced and smooth

**Sign-off:** _______________ Date: _______________

---

## Notes

Use this space to document any issues found during testing:

```
Issue 1: [Description]
Severity: [Critical/High/Medium/Low]
Status: [Open/Fixed/Deferred]

Issue 2: [Description]
...
```

## Test Environment

- **Python Version:** _____________
- **Streamlit Version:** _____________
- **OS:** _____________
- **Browser:** _____________
- **Date:** _____________

---

**Testing completed by:** _______________

**Ready for deployment:** [ ] Yes [ ] No

**Notes:** _______________
