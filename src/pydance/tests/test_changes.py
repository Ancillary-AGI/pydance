#!/usr/bin/env python3
"""
Test script to verify our changes work correctly
"""

import sys

def test_logging():
    """Test that logging works correctly"""
    print("Testing logging functionality...")

    try:
        from pydance.utils.logging import get_logger, LogLevel

        # Test basic logging
        logger = get_logger('test_logger')
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")

        # Test context
        logger.set_context(user_id="123", request_id="abc")
        logger.info("Message with context")

        print("✓ Logging functionality works")
        return True
    except Exception as e:
        print(f"✗ Logging test failed: {e}")
        return False

def test_form_validation():
    """Test that form validation works"""
    print("Testing form validation functionality...")

    try:
        from pydance.utils.form_validation import Form, CharField, EmailField

        class TestForm(Form):
            name = CharField(required=True, max_length=100)
            email = EmailField(required=True)

        # Test valid form
        form = TestForm({'name': 'John Doe', 'email': 'john@example.com'})
        assert form.is_valid()
        assert form.cleaned_data['name'] == 'John Doe'
        assert form.cleaned_data['email'] == 'john@example.com'

        # Test invalid form
        form = TestForm({'name': '', 'email': 'invalid-email'})
        assert not form.is_valid()
        assert 'name' in form.errors
        assert 'email' in form.errors

        print("✓ Form validation functionality works")
        return True
    except Exception as e:
        print(f"✗ Form validation test failed: {e}")
        return False

async def test_template_form_errors():
    """Test that template form errors work"""
    print("Testing template form errors functionality...")

    try:
        from pydance.utils.form_validation import Form, CharField
        import tempfile

        class TestForm(Form):
            name = CharField(required=True)

        # Create a temporary template directory
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = LeanTemplateEngine(temp_dir)

            # Create a test template
            template_content = """
            <form>
                <input name="name" value="{{ form.data.name }}">
                {% form_errors form %}
                <div class="error">{{ error }}</div>
                {% endform_errors %}
            </form>
            """

            # Test with invalid form
            form = TestForm({'name': ''})
            form.is_valid()

            print(f"Form errors: {form.errors}")
            print(f"Form data: {form.data}")

            context = {'form': form}
            result = await engine.render_string(template_content, context)

            print(f"Template result: {result}")

            # Should contain error message
            assert 'Validation error:' in result or 'This field is required' in result
            print("✓ Template form errors functionality works")
            return True
    except Exception as e:
        print(f"✗ Template form errors test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("Running verification tests...\n")

    results = []
    results.append(test_logging())
    results.append(test_form_validation())
    results.append(await test_template_form_errors())

    print(f"\nResults: {sum(results)}/{len(results)} tests passed")

    if all(results):
        print("🎉 All tests passed! Changes are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == '__main__':
    import asyncio
    sys.exit(asyncio.run(main()))
