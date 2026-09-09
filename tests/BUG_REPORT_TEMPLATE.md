# Bug Report Template

**Instructions**: Copy this template when filing a new bug. Fill in all sections completely. Attach screenshots, code samples, or error logs as needed.

---

## Bug ID: BUG-XXX

**Discovered**: YYYY-MM-DD
**Reporter**: [QA Agent / Tester Name]
**Assigned To**: [Programmer Agent / Developer Name]

---

## Summary

**Brief Description** (1-2 sentences):
```
[Clear, concise description of what's wrong]
```

---

## Bug Details

### Operations Class
```
[e.g., ScrBookOperations, WfiAnalysisOperations, ReversalEntryOperations]
```

### Method/Function
```
[e.g., Create(canonical_num, name=None), AddSense(entry, sense), GetForm(obj, wsHandle)]
```

### Test Case (if applicable)
```
[e.g., Test_Create_MinimalBook, Test_Integration_BidirectionalSenseLinking]
```

---

## Expected Behavior

**What should happen**:
```
[Describe the correct/expected behavior in detail]

Example:
- Create() should return a valid IScrBook object
- Book should appear in Scripture.ScriptureBooksOS
- Book.CanonicalNum should be set to the provided value
- Book.Guid should not be empty
```

---

## Actual Behavior

**What actually happens**:
```
[Describe what actually occurred]

Example:
- Create() returns None
- No book appears in Scripture.ScriptureBooksOS
- No error is raised
```

---

## Steps to Reproduce

**Reproducible**: ⬜ Always | ⬜ Sometimes | ⬜ Rarely

**Steps**:
```
1. Open FLEx project: "TestProject_Scripture"
2. Initialize flexlibs:
   from flexicon import FLExProject
   project = FLExProject()
   project.OpenProject("TestProject_Scripture", writeEnabled=True)
3. Call method:
   book = project.ScrBooks.Create(1)
4. Observe result:
   print(book)  # Prints None instead of book object
```

---

## Error Message / Traceback

**Console Output**:
```
[Paste complete error traceback or error message]

Example:
Traceback (most recent call last):
  File "test_scripture.py", line 45, in test_create_book
    book = project.ScrBooks.Create(1)
  File "D:\Github\flexlibs\flexlibs\code\Scripture\ScrBookOperations.py", line 123, in Create
    factory = self.project.project.ServiceLocator.GetService(IScrBookFactory)
AttributeError: 'NoneType' object has no attribute 'GetService'
```

**FLEx Error Dialog** (if applicable):
```
[Describe any error dialogs shown in FLEx GUI]
```

---

## Screenshots

**Attach Screenshots**:
- [ ] Console/terminal showing error
- [ ] FLEx GUI showing incorrect display
- [ ] Debugger showing object state
- [ ] Comparison with expected behavior

**Screenshot Descriptions**:
```
1. screenshot_error.png - Shows AttributeError in console
2. screenshot_flex_empty.png - Shows empty Scripture view (book not created)
3. screenshot_debugger.png - Shows factory variable is None
```

---

## Environment

### System Information
- **OS**: [e.g., Windows 10 Pro 64-bit, macOS 12.6, Ubuntu 22.04]
- **Python Version**: [e.g., 3.9.7]
- **FLEx Version**: [e.g., 9.1.22 Beta]
- **flexlibs Version**: [e.g., 0.5.0]

### Project Information
- **Test Project Name**: [e.g., TestProject_Scripture]
- **Project Type**: [Scripture, Dictionary, Grammar, etc.]
- **Project Size**: [Small (<100 entries), Medium (100-1000), Large (>1000)]
- **Writing Systems**: [e.g., en, es, qaa-x-test]

### Test Environment
- **Test Framework**: [e.g., unittest, pytest, manual testing]
- **Test Project Location**: [e.g., D:\FLEx\Projects\TestProject]
- **Backup Available**: ⬜ Yes | ⬜ No

---

## Impact

### Severity
- [ ] **Critical** - Blocks release (data corruption, crash, core functionality broken)
- [ ] **High** - Major functionality broken (no workaround available)
- [ ] **Medium** - Functionality impaired (workaround available)
- [ ] **Low** - Cosmetic, edge case, or minor issue

### Priority
- [ ] **P0** - Fix immediately (data loss risk)
- [ ] **P1** - Fix before release (blocks testing)
- [ ] **P2** - Fix in next sprint (reduces functionality)
- [ ] **P3** - Fix when time permits (nice to have)

### Affected Areas
- [ ] Create operations
- [ ] Find operations
- [ ] GetAll operations
- [ ] Delete operations
- [ ] Property get/set
- [ ] Parent-child relationships
- [ ] Cross-references
- [ ] Writing system handling
- [ ] Error handling
- [ ] FLEx GUI display
- [ ] Data persistence
- [ ] Export/import

### User Impact
```
[Describe how this bug affects users]

Example:
- Users cannot create scripture books via flexlibs
- Workaround: Use FLEx GUI to create books manually
- Blocks automated scripture import workflows
```

---

## Root Cause Analysis (if known)

**Suspected Cause**:
```
[If you've investigated, describe what you think is causing the bug]

Example:
- ServiceLocator not initialized properly
- self.project.project is None at time of factory access
- Missing initialization step in __init__
```

**Code Location**:
```
File: D:\Github\flexlibs\flexlibs\code\Scripture\ScrBookOperations.py
Line: 123
Method: Create()

Problematic code:
    factory = self.project.project.ServiceLocator.GetService(IScrBookFactory)
    # self.project.project is None here
```

---

## Suggested Fix

**Proposed Solution** (if known):
```
[Describe how this could be fixed]

Example:
1. Add null check before accessing ServiceLocator:
   if not self.project or not self.project.project:
       raise FP_ParameterError("Project not properly initialized")

2. Ensure project.project is set in FLExProject.OpenProject()

3. Add initialization verification in __init__:
   if not hasattr(self.project, 'project') or self.project.project is None:
       raise FP_ParameterError("Invalid project instance")
```

**Workaround** (temporary solution):
```
[If there's a way to work around this bug, describe it]

Example:
- Create books manually in FLEx GUI
- Use project.ObjectsIn(IScrBookRepository) to access existing books
- Wait for fix before testing Create functionality
```

---

## Testing Notes

### How Discovered
```
[Describe how this bug was found]

Example:
- Running Test_Create_MinimalBook from scripture_operations_tests.md
- Step 1 of "Scripture Import Scenario" integration test
- Manual testing of demo_scripture_operations.py
```

### Verification Steps
```
[Steps to verify the bug is fixed]

1. Run Test_Create_MinimalBook
2. Verify book object returned (not None)
3. Verify book.CanonicalNum == 1
4. Verify book in Scripture.ScriptureBooksOS
5. Open project in FLEx GUI
6. Verify book displays correctly
7. Close and reopen - verify persistence
```

### Regression Impact
```
[Could this fix break other functionality?]

Example:
- Fix should not affect other Operations classes
- May affect any code that assumes project.project is always valid
- Need to test all Create methods after fix
```

---

## Related Issues

### Related Bugs
- [ ] BUG-XXX - Similar issue in different class
- [ ] BUG-XXX - Depends on this fix

### Related Test Cases
- Test_Create_MinimalBook
- Test_Create_BookWithName
- Test_Integration_AddSectionToBook

### Related Code
```
Files that may need changes:
- D:\Github\flexlibs\flexlibs\code\Scripture\ScrBookOperations.py
- D:\Github\flexlibs\flexlibs\FLExProject.py (initialization)
- D:\Github\flexlibs\flexlibs\code\BaseOperations.py (if common issue)
```

---

## Status Tracking

### Current Status
- [ ] **Open** - Bug reported, not yet triaged
- [ ] **Confirmed** - Bug reproduced and confirmed
- [ ] **In Progress** - Developer working on fix
- [ ] **Fixed** - Fix implemented, awaiting verification
- [ ] **Verified** - Fix verified by QA
- [ ] **Closed** - Bug resolved and verified

### Resolution
- [ ] **Fixed** - Bug was fixed
- [ ] **Won't Fix** - Bug will not be fixed (document reason)
- [ ] **Duplicate** - Duplicate of another bug (reference bug ID)
- [ ] **Not a Bug** - Expected behavior (document why)
- [ ] **Cannot Reproduce** - Unable to reproduce bug

### Timeline
| Date | Status | Notes |
|------|--------|-------|
| 2025-12-05 | Open | Bug reported by QA Agent |
| | | |
| | | |

---

## Communication

### Notifications Sent
- [ ] Programmer Agent responsible for class
- [ ] Project Lead
- [ ] Other QA testers

### Discussion Thread
```
[Link to discussion in GitHub Issues, Slack, email thread, etc.]
```

### External References
- FLEx Documentation: [link if applicable]
- LCM API Documentation: [link if applicable]
- Similar issues in other projects: [link if applicable]

---

## Attachments

### Files to Attach
- [ ] Error log file
- [ ] Test script that reproduces bug
- [ ] FLEx project (if small and safe to share)
- [ ] Database dump (if relevant)
- [ ] Screenshots (see Screenshots section above)

### Attachment List
```
1. error_log_2025-12-05.txt - Full error log from test run
2. test_reproduce_bug.py - Standalone script to reproduce bug
3. screenshot_error.png - Console showing error
4. screenshot_flex.png - FLEx GUI showing issue
```

---

## Verification

### After Fix Applied

**Verification Date**: __________
**Verified By**: __________

**Verification Results**:
- [ ] Bug is fixed
- [ ] No regression introduced
- [ ] All related test cases pass
- [ ] Manual verification in FLEx GUI successful
- [ ] Documentation updated (if needed)

**Verification Notes**:
```
[Describe verification testing performed]

Example:
- Ran Test_Create_MinimalBook - PASS
- Ran all ScrBookOperations tests - ALL PASS
- Created book manually in demo script - SUCCESS
- Verified book displays in FLEx GUI - SUCCESS
- Tested close/reopen - book persists - SUCCESS
- No regression in other Operations classes
```

---

## Additional Notes

```
[Any other relevant information, context, or observations]

Example:
- This bug affects all Scripture Operations classes that use factories
- Similar pattern may exist in Discourse Operations
- Consider reviewing all factory usage for null checks
- May want to add defensive programming throughout
```

---

**Bug Report Template Version**: 1.0
**Last Updated**: 2025-12-05

---

## Filing Instructions

### How to File a Bug

1. **Copy this template** to a new file: `BUG-XXX_short_description.md`
2. **Assign Bug ID**: Use next available number (BUG-001, BUG-002, etc.)
3. **Fill in all sections**: Don't leave blanks - write "N/A" if not applicable
4. **Attach files**: Include screenshots, logs, test scripts
5. **Save to**: `D:\Github\flexlibs\tests\bugs\` directory
6. **Update log**: Add bug to `test_execution_log.md`
7. **Notify**: Alert programmer agent responsible for the class
8. **Track**: Update status as bug progresses through resolution

### Bug ID Naming Convention

- **BUG-001 to BUG-099**: Scripture Operations bugs
- **BUG-100 to BUG-199**: Discourse Operations bugs
- **BUG-200 to BUG-299**: Reversal & Wordform Operations bugs
- **BUG-300+**: General/cross-cutting bugs

### Priority Guidelines

**P0 - Critical**:
- Data corruption or data loss
- Crashes or unhandled exceptions
- Cannot create or access objects at all
- Blocks all further testing

**P1 - High**:
- Major functionality completely broken
- No workaround available
- Blocks significant testing
- Incorrect data written to database

**P2 - Medium**:
- Functionality impaired but workaround exists
- Some test cases fail but others pass
- Display issues in FLEx GUI
- Missing or incorrect error messages

**P3 - Low**:
- Cosmetic issues
- Edge cases
- Documentation errors
- Nice-to-have features

---

## Example Bug Report

See: `BUG-001_ScrBookOperations_Create_returns_None.md` (if available)

---

**Questions?** Contact QA Lead or Project Manager.
