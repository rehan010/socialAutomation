from django import template

register = template.Library()


def any(post):
    if post.post_urn.all():
        for urn in post.post_urn.all():
                provider = urn.org.provider
                if provider == 'facebook':
                    return True

    return False

def sub(value, arg):
    """
    Custom template filter to subtract arg from value.
    """
    return value - arg

def company_value(value):
    if isinstance(value, list) and len(value) > 0:
        # Get the first element of the list
        field = value[0]

        # Check if the first element is a string representing an integer
        if isinstance(field, str) and field.isdigit():
            # Convert the string to an integer and return it
            return int(field)

        # Default case: return the original value
    return value

register.filter('company_value', company_value)
register.filter('any', any)
register.filter('sub', sub)