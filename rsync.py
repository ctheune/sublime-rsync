import os.path
import sublime
import sublime_plugin
import subprocess
import threading


class SyncViewThread(threading.Thread):

    def __init__(self, sync, base_path):
        self.source = os.path.join(base_path, sync['source'])
        self.target = sync['target']
        self.args = sync.get('args', '')
        self.command = 'rsync -avz --delete {0} {1} {2}'.format(
            self.args, self.source, self.target)
        print("Syncing via:", self.command)
        self.success = None
        self.exception = None
        super(SyncViewThread, self).__init__()

    def run(self):
        try:
            subprocess.check_call(self.command, shell=True)
        except Exception as e:
            self.exception = e
            self.success = False
        else:
            self.success = True


class Rsync(sublime_plugin.EventListener):

    def on_post_save(self, view):
        project = view.window().project_data()
        if project is None:
            return
        base_path = os.path.dirname(view.window().project_file_name())
        threads = []
        syncs = project.get('rsync', [])
        if not syncs:
            return
        for sync in syncs:
            t = SyncViewThread(sync, base_path)
            t.start()
            threads.append(t)

        def watch_threads():
            alive = done = errors = 0
            for t in threads[:]:
                if t.isAlive():
                    alive += 1
                elif t.success:
                    done += 1
                else:
                    print(t.exception)
                    threads.remove(t)
                    errors += 1

            if alive:
                view.set_status(
                    'rsync',
                    'Syncing (done={}, running={}, failed={})'.format(
                        done, alive, errors))
                sublime.set_timeout(watch_threads, 100)
            elif errors:
                view.set_status('rsync', 'Sync finished with errors.')
            else:
                view.set_status('rsync', 'Sync finished - success')

        watch_threads()

# onsave:
#  - use project-specific configuration variables:
#    - exclude lists (provide some defaults, '.svn', '.git', '.hg' ...)
