import os.path

VERSION = (1, 0, 0, 'dev')


def get_version():
    """
    Return the version as a string. If this is flagged as a development
    release and mercurial can be loaded the specifics about the changeset
    will be appended to the version string. 
    """
    build_info = tuple()
    if 'dev' in VERSION:
        try:
            from mercurial import hg, ui
    
            repo_path = os.path.join(os.path.dirname(__file__), '..')
            repo = hg.repository(ui.ui(), repo_path)
            ctx = repo['tip']
            build_info += (ctx.branch(), '%s:%s' % (ctx.rev(), str(ctx)))
        except:
            # mercurial module missing or repository not found
            build_info += ('unknown',)
    v = VERSION + build_info
    return '.'.join(map(str, v[:3] + ('_'.join(map(str, v[3:])),)))
