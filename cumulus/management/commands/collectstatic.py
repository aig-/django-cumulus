import hashlib

from django.contrib.staticfiles.management.commands import collectstatic

from cumulus.storage import SwiftclientStorage


class Command(collectstatic.Command):

    def delete_file(self, path, prefixed_path, source_storage):
        """
        Checks if the target file should be deleted if it already exists
        """
        if isinstance(self.storage, SwiftclientStorage):
            if self.storage.exists(prefixed_path):
                try:
                    etag = self.storage._get_cloud_obj(prefixed_path).etag
                    digest = "{0}".format(hashlib.md5(source_storage.open(path).read()).hexdigest())
                    print etag, digest
                    if etag == digest:
                        self.log(u"Skipping '{0}' (not modified based on file hash)".format(path))
                        return False
                except:
                    raise
        return super(Command, self).delete_file(path, prefixed_path, source_storage)
        
    def copy_file(self, path, prefixed_path, source_storage):
        """
        Attempt to copy ``path`` with storage
        """
        # Skip this file if it was already copied earlier
        if prefixed_path in self.copied_files:
            return self.log("Skipping '%s' (already copied earlier)" % path)
        # Delete the target file if needed or break
        if not self.delete_file(path, prefixed_path, source_storage):
            return
        # The full path of the source file
        source_path = source_storage.path(path)
        # Finally start copying
        if self.dry_run:
            self.log("Pretending to copy '%s'" % source_path, level=1)
        else:
            self.log("Copying '%s'" % source_path, level=1)
            if self.local:
                full_path = self.storage.path(prefixed_path)
                try:
                    os.makedirs(os.path.dirname(full_path))
                except OSError:
                    pass
            with source_storage.open(path) as source_file:
                self.storage.save(prefixed_path, source_file)
        if not prefixed_path in self.copied_files:
            self.copied_files.append(prefixed_path)