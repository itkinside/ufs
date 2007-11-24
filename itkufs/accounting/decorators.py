from itkufs.accounting.models import *

def is_group_admin(function):
    def wrapped(request, *args, **kwargs):
        if 'group' in kwargs:
            try:
                group = Group.objects.get(slug=kwargs['group'])
            except Group.DoesNotExist:
                raise Http404


            if group.admins.filter(id=request.user.id).count():
                kwargs['is_admin'] = True
            else:
                kwargs['is_admin'] = False

            return function(request, *args, **kwargs)
        else:
            raise Exception('You can only decorate methods that take a kwarg group=group.slug')
    return wrapped
