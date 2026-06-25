"""
Phase 9 — AI Agent Audit
Verify all agent files for imports, error handling, pipeline connections.
"""
import sys
import os
import ast
import importlib
import traceback
from typing import Dict, List, Tuple

sys.path.insert(0, '.')

# ═══════════════════════════════════════════════════════════════════
# AUDIT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def check_imports(file_path: str) -> Dict:
    """Check if all imports in a file work."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse AST to find imports
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    try:
                        importlib.import_module(alias.name)
                    except ImportError as e:
                        issues.append(f"Import failed: {alias.name} - {e}")
                    except Exception as e:
                        issues.append(f"Import error: {alias.name} - {e}")
            
            elif isinstance(node, ast.ImportFrom):
                try:
                    module = importlib.import_module(node.module or '')
                    for alias in node.names:
                        try:
                            getattr(module, alias.name)
                        except AttributeError:
                            issues.append(f"Attribute not found: {node.module}.{alias.name}")
                except ImportError as e:
                    issues.append(f"Module import failed: {node.module} - {e}")
                except Exception as e:
                    issues.append(f"Import error: {node.module} - {e}")
        
        return {
            "file": file_path,
            "issues": issues,
            "issue_count": len(issues),
            "status": "PASS" if not issues else "FAIL"
        }
    
    except Exception as e:
        return {
            "file": file_path,
            "issues": [f"File parse error: {e}"],
            "issue_count": 1,
            "status": "ERROR"
        }

def check_circular_imports(file_path: str) -> Dict:
    """Check for circular imports."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith('agents'):
                    imports.append(node.module)
        
        # Check if any imported module imports back to this file
        file_module = file_path.replace('\\', '.').replace('/', '.').replace('.py', '')
        for imp in imports:
            if imp in file_module or file_module.endswith(imp):
                issues.append(f"Potential circular import: {imp}")
        
        return {
            "file": file_path,
            "issues": issues,
            "issue_count": len(issues),
            "status": "PASS" if not issues else "WARNING"
        }
    
    except Exception as e:
        return {
            "file": file_path,
            "issues": [f"Error checking circular imports: {e}"],
            "issue_count": 1,
            "status": "ERROR"
        }

def check_error_handling(file_path: str) -> Dict:
    """Check for proper error handling."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Check for bare except clauses
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append(f"Bare except clause at line {node.lineno}")
        
        # Check for missing try-except in critical functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name in ('run', 'execute', 'process', 'code'):
                    has_try = False
                    for child in ast.walk(node):
                        if isinstance(child, ast.Try):
                            has_try = True
                            break
                    if not has_try:
                        issues.append(f"Critical function '{node.name}' missing try-except")
        
        return {
            "file": file_path,
            "issues": issues,
            "issue_count": len(issues),
            "status": "PASS" if not issues else "FAIL"
        }
    
    except Exception as e:
        return {
            "file": file_path,
            "issues": [f"Error checking error handling: {e}"],
            "issue_count": 1,
            "status": "ERROR"
        }

def check_pipeline_connections(file_path: str) -> Dict:
    """Check if pipeline stages are connected properly."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for pipeline-related patterns
        if 'pipeline' in file_path.lower() or 'pipeline' in content.lower():
            # Check for stage connections
            if 'stage' in content.lower() and '->' not in content and '>>' not in content:
                issues.append("Pipeline stages may not be properly connected")
        
        # Check for method chaining
        if 'self._' in content and 'return self' not in content:
            # Check if methods return values for chaining
            pass  # Not all pipelines need method chaining
        
        return {
            "file": file_path,
            "issues": issues,
            "issue_count": len(issues),
            "status": "PASS" if not issues else "WARNING"
        }
    
    except Exception as e:
        return {
            "file": file_path,
            "issues": [f"Error checking pipeline connections: {e}"],
            "issue_count": 1,
            "status": "ERROR"
        }

def check_training_cases(file_path: str) -> Dict:
    """Check if training case loading works."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'training_cases' in content.lower() or 'get_case_answer' in content:
            # Try to import training cases
            try:
                from knowledge.training_cases_v19 import get_case_answer, search_cases, get_all_cases
                cases = get_all_cases()
                if not cases:
                    issues.append("Training cases loaded but empty")
            except Exception as e:
                issues.append(f"Training case loading failed: {e}")
        
        return {
            "file": file_path,
            "issues": issues,
            "issue_count": len(issues),
            "status": "PASS" if not issues else "FAIL"
        }
    
    except Exception as e:
        return {
            "file": file_path,
            "issues": [f"Error checking training cases: {e}"],
            "issue_count": 1,
            "status": "ERROR"
        }

def check_book_engine(file_path: str) -> Dict:
    """Check if book engine integration works."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'book_engine' in content.lower() or 'cpt_book' in content.lower() or 'icd_book' in content.lower():
            # Try to import book engines
            try:
                from knowledge.cpt_book_engine import get_engine as get_cpt_engine
                from knowledge.icd_book_engine import get_engine as get_icd_engine
                cpt_engine = get_cpt_engine()
                icd_engine = get_icd_engine()
                if not cpt_engine or not icd_engine:
                    issues.append("Book engines returned None")
            except Exception as e:
                issues.append(f"Book engine loading failed: {e}")
        
        return {
            "file": file_path,
            "issues": issues,
            "issue_count": len(issues),
            "status": "PASS" if not issues else "FAIL"
        }
    
    except Exception as e:
        return {
            "file": file_path,
            "issues": [f"Error checking book engine: {e}"],
            "issue_count": 1,
            "status": "ERROR"
        }

# ═══════════════════════════════════════════════════════════════════
# MAIN AUDIT
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 80)
    print("PHASE 9 — AI AGENT AUDIT")
    print("Checking all agent files for imports, error handling, pipeline connections")
    print("=" * 80)
    print()
    
    # Files to audit
    agent_files = [
        "agents/medcode_deterministic_pipeline.py",
        "agents/clinical_note_parser.py",
        "agents/graceful_degradation.py",
        "agents/orchestrator.py",
        "agents/coder_agent.py",
        "agents/deterministic_rule_engine.py",
        "agents/reviewer_agent.py",
        "agents/auditor_agent.py",
        "agents/adjuster_agent.py",
        "agents/workflow_controller.py",
        "agents/v14_pipeline.py",
        "agents/v15_pipeline.py",
        "agents/v17_pipeline_integration.py",
        "agents/v19_pipeline.py",
        "agents/v17/v17_pipeline.py",
    ]
    
    results = []
    total_issues = 0
    
    for file_path in agent_files:
        print(f"\n{'='*80}")
        print(f"Auditing: {file_path}")
        print(f"{'='*80}")
        
        full_path = os.path.join('.', file_path)
        if not os.path.exists(full_path):
            print(f"  [SKIP] File not found")
            continue
        
        # Run all checks
        import_check = check_imports(full_path)
        circular_check = check_circular_imports(full_path)
        error_check = check_error_handling(full_path)
        pipeline_check = check_pipeline_connections(full_path)
        training_check = check_training_cases(full_path)
        book_check = check_book_engine(full_path)
        
        # Print results
        print(f"\n  Import Check: {import_check['status']}")
        for issue in import_check['issues']:
            print(f"    [ISSUE] {issue}")
        
        print(f"  Circular Import Check: {circular_check['status']}")
        for issue in circular_check['issues']:
            print(f"    [WARNING] {issue}")
        
        print(f"  Error Handling Check: {error_check['status']}")
        for issue in error_check['issues']:
            print(f"    [ISSUE] {issue}")
        
        print(f"  Pipeline Connection Check: {pipeline_check['status']}")
        for issue in pipeline_check['issues']:
            print(f"    [WARNING] {issue}")
        
        print(f"  Training Case Check: {training_check['status']}")
        for issue in training_check['issues']:
            print(f"    [ISSUE] {issue}")
        
        print(f"  Book Engine Check: {book_check['status']}")
        for issue in book_check['issues']:
            print(f"    [ISSUE] {issue}")
        
        # Calculate total issues for this file
        file_issues = (
            import_check['issue_count'] +
            circular_check['issue_count'] +
            error_check['issue_count'] +
            pipeline_check['issue_count'] +
            training_check['issue_count'] +
            book_check['issue_count']
        )
        total_issues += file_issues
        
        results.append({
            "file": file_path,
            "import_check": import_check,
            "circular_check": circular_check,
            "error_check": error_check,
            "pipeline_check": pipeline_check,
            "training_check": training_check,
            "book_check": book_check,
            "total_issues": file_issues,
        })
    
    # ═══════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 9 SUMMARY")
    print("=" * 80)
    print(f"Files Audited: {len(results)}")
    print(f"Total Issues Found: {total_issues}")
    print(f"Files with Issues: {sum(1 for r in results if r['total_issues'] > 0)}")
    print(f"Files without Issues: {sum(1 for r in results if r['total_issues'] == 0)}")
    print()
    
    # Save results
    import json
    with open("phase9_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("Results saved to phase9_results.json")
    
    return results

if __name__ == "__main__":
    main()
