from django import template

register = template.Library()


def any(post):
    if post.post_urn.all():
        for urn in post.post_urn.all():
                provider = urn.org.provider
                print(provider)
                if provider == 'facebook':
                    return True

    return False

register.filter('any', any)