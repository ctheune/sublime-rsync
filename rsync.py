import sublime, sublime_plugin
import subprocess
import StringIO

class SyncViewThread(threading.Thread):

    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.success = None
        self.exception = None
        super(SyncViewThread, self).__init__()

    def run(self):
        try:
            subprocess.check_call(
                'rsync -avz --delete --exclude ".hg" {0} {1}'.format(
                    self.source, self.target), shell=True)
        except Exception, e:
            self.exception = e
            self.success = False
        else:
            self.success = True


class Rsync(sublime_plugin.EventListener):


    def on_post_save(self, view):
        settings = view.settings()
        if not settings.has('rsync-target'):
            view.set_status('rsync', '')
            return

        t = SyncViewThread(settings.get('rsync-source'),
                           settings.get('rsync-target'))
        t.start()

        def watch_thread():
            if t.isAlive():
                view.set_status('rsync', 'Rsync: syncing ...')
                sublime.set_timeout(watch_thread, 100)
                return
            if t.success:
                view.set_status('rsync', 'Rsync: up to date.')
            else:
                view.set_status('rsync', 'Rsync: error.')
                print t.exception

        watch_thread()

    # def
# onsave:
#- check whether project has an rsync remote -> update remote, signal "in progress" and "done" in status bar
#- use project-specific configuration variables:
#    - where to sync to
#    - exclude lists (provide some defaults, '.svn', '.git', '.hg' ...)
