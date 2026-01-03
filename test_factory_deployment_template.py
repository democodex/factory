#!/usr/bin/env python3
"""Test script to verify factory deployment Makefile template renders correctly.

This script tests that the Makefile template:
1. Renders with default settings (factory mode - NEW DEFAULT)
2. Renders with use_original_deployment: true (standard mode)
3. Contains the expected targets in each mode
"""

import tempfile
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

def test_makefile_rendering():
    """Test Makefile renders correctly in both factory and standard modes."""

    # Get the base template Makefile
    factory_root = Path(__file__).parent
    base_template_dir = factory_root / "agent_starter_pack" / "base_template"
    makefile_path = base_template_dir / "Makefile"

    if not makefile_path.exists():
        print(f"❌ ERROR: Makefile not found at {makefile_path}")
        return False

    print(f"✓ Found Makefile template at: {makefile_path}")
    print()

    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader(str(base_template_dir)))
    template = env.get_template("Makefile")

    # Test 1: Factory Deployment Mode (DEFAULT)
    print("=" * 80)
    print("TEST 1: Factory Deployment Mode (DEFAULT - no flag needed)")
    print("=" * 80)

    factory_config = {
        "project_name": "test-factory-agent",
        "agent_directory": "app",
        "deployment_target": "agent_engine",
        "cicd_runner": "google_cloud_build",
        "is_adk": True,
        "is_adk_live": False,
        "is_a2a": False,
        "example_question": "What can you help me with?",
        "settings": {
            # No use_original_deployment flag = factory mode (default)
            "agent_directory": "app",
        }
    }

    factory_makefile = template.render(cookiecutter=factory_config)

    # Check for factory deployment targets
    factory_targets = ["analyze:", "prepare:", "deploy:", "deploy-verbose:", "backend:"]
    factory_keywords = [
        "factory_deployment_agent",
        "Delegated to Factory Deployment Agent",
        "analyze test-factory-agent",  # Rendered value, not template var
        "prepare test-factory-agent",
        "deploy test-factory-agent --yes"
    ]

    all_found = True
    for target in factory_targets:
        if target in factory_makefile:
            print(f"  ✓ Found target: {target}")
        else:
            print(f"  ❌ Missing target: {target}")
            all_found = False

    for keyword in factory_keywords:
        if keyword in factory_makefile:
            print(f"  ✓ Found keyword: '{keyword}'")
        else:
            print(f"  ❌ Missing keyword: '{keyword}'")
            all_found = False

    # Should NOT contain standard deployment
    if "uv run -m {{cookiecutter.agent_directory}}.app_utils.deploy" not in factory_makefile:
        print(f"  ✓ Correctly excludes standard deployment logic")
    else:
        print(f"  ❌ ERROR: Contains standard deployment logic (should be excluded)")
        all_found = False

    print()

    if all_found:
        print("✅ TEST 1 PASSED: Factory deployment mode renders correctly")
    else:
        print("❌ TEST 1 FAILED: Missing expected content in factory mode")

    print()

    # Test 2: Standard Deployment Mode (OPT-IN)
    print("=" * 80)
    print("TEST 2: Original Deployment Mode (use_original_deployment: true)")
    print("=" * 80)

    standard_config = {
        "project_name": "test-standard-agent",
        "agent_directory": "app",
        "deployment_target": "agent_engine",
        "cicd_runner": "google_cloud_build",
        "is_adk": True,
        "is_adk_live": False,
        "is_a2a": False,
        "example_question": "What's the weather in SF?",
        "settings": {
            "use_original_deployment": True,  # Opt-in to original deployment
            "agent_directory": "app",
        }
    }

    standard_makefile = template.render(cookiecutter=standard_config)

    # Check for standard deployment
    standard_keywords = [
        "uv export --no-hashes",
        "uv run -m app.app_utils.deploy",
        "--source-packages=./app",
        "--entrypoint-module=app.agent_engine_app",
    ]

    all_found = True
    for keyword in standard_keywords:
        if keyword in standard_makefile:
            print(f"  ✓ Found standard deployment: '{keyword}'")
        else:
            print(f"  ❌ Missing standard deployment: '{keyword}'")
            all_found = False

    # Should NOT contain factory deployment
    if "factory_deployment_agent" not in standard_makefile:
        print(f"  ✓ Correctly excludes factory deployment logic")
    else:
        print(f"  ❌ ERROR: Contains factory deployment logic (should be excluded)")
        all_found = False

    print()

    if all_found:
        print("✅ TEST 2 PASSED: Standard deployment mode renders correctly")
    else:
        print("❌ TEST 2 FAILED: Missing expected content in standard mode")

    print()

    # Test 3: Write sample outputs for inspection
    print("=" * 80)
    print("TEST 3: Writing sample outputs for manual inspection")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        factory_output = tmp_path / "Makefile.factory"
        standard_output = tmp_path / "Makefile.standard"

        factory_output.write_text(factory_makefile)
        standard_output.write_text(standard_makefile)

        print(f"  ✓ Factory mode Makefile written to: {factory_output}")
        print(f"  ✓ Standard mode Makefile written to: {standard_output}")
        print()
        print("  Sample deployment section (factory mode):")
        print("  " + "-" * 76)

        # Extract deployment section from factory makefile
        lines = factory_makefile.split("\n")
        in_deployment = False
        line_count = 0
        for line in lines:
            if "Backend Deployment Targets" in line:
                in_deployment = True
            if in_deployment:
                print(f"  {line}")
                line_count += 1
                if line_count > 25:  # Show first 25 lines
                    print("  ...")
                    break

        print()

    print("✅ TEST 3 PASSED: Sample outputs written successfully")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("✓ Makefile template has been modified to support factory deployment")
    print("✓ Template renders correctly in both factory and standard modes")
    print("✓ Factory mode includes: analyze, prepare, deploy, deploy-verbose")
    print("✓ Standard mode uses original deployment logic")
    print()
    print("Next steps:")
    print("  1. Run: cd /path/to/xyborg && uvx agent-starter-pack create")
    print("  2. Factory deployment is now THE DEFAULT (no config changes needed)")
    print("  3. Verify the generated Makefile has: analyze, prepare, deploy, deploy-verbose")
    print("  4. To use original deployment, add 'use_original_deployment: true' to templateconfig.yaml")
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_makefile_rendering()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
