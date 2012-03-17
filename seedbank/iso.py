"""
Copyright 2009-2012 Jasper Poppe <jpoppe@ebay.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

#FIXME: Debian 32 BIT support

__author__ = 'Jasper Poppe <jpoppe@ebay.com>'
__copyright__ = 'Copyright (c) 2009-2012 Jasper Poppe'
__credits__ = ''
__license__ = 'Apache License, Version 2.0'
__version__ = '2.0.0rc3'
__maintainer__ = 'Jasper Poppe'
__email__ = 'jpoppe@ebay.com'
__status__ = 'production'

import os

import utils


class Build:

    def __init__(self, cfg, iso_file, fqdn, dst):
        """prepare the data dictionary"""
        self.data = {}
        self.cfg = cfg
        work_path = os.path.join(cfg['paths']['temp'], 'seedbank', fqdn, 'iso')
        self.work_path = work_path
        self.work_initrd = os.path.join(work_path, 'initrd')
        self.work_iso = os.path.join(work_path, 'iso')
        self.iso_file = iso_file
        self.iso_dst = dst

    def prepare(self):
        """remove temporary files, create the directory structure"""
        utils.rmtree(self.work_path)
        utils.make_dirs(os.path.join(self.work_iso, 'seedbank/etc/runonce.d'))
        utils.make_dirs(self.work_initrd)
        utils.run('bsdtar -C "%s" -xf "%s"' % (self.work_iso, self.iso_file))
        utils.run('chmod -R u+w "%s"' % self.work_iso)

    def add_templates(self):
        """process and add the rc.local and isolinux templates"""
        path = self.cfg['paths']['templates']
        src = os.path.join(path, self.cfg['templates']['isolinux'])
        dst = os.path.join(self.work_iso, 'isolinux/isolinux.cfg')
        utils.write_template(self.data, src, dst)
        src = os.path.join(path, self.cfg['templates']['rc_local'])
        dst = os.path.join(self.work_iso, 'seedbank/etc/rc.local')
        utils.write_template(self.data, src, dst)

    def add_preseed(self, contents):
        """add the seed file to the intrd image"""
        dst = os.path.join(self.work_initrd, 'preseed.cfg')
        utils.file_write(dst, contents)
        initrd = os.path.join(self.work_iso, 'install.amd',
            'initrd.gz')
        utils.initrd_extract(self.work_initrd, initrd)
        utils.initrd_create(self.work_initrd, initrd)

    def add_overlay(self, path):
        """create a tar archive of the given overlay"""
        utils.run('cd "%s" && %s -cf "%s/overlay.tar" *' % (path, 'tar',
            self.work_iso))

    def add_puppet_manifests(self, fqdn):
        """copy the Puppet manifests to the ISO"""
        path = os.path.join(self.cfg['paths']['temp'], 'seedbank', fqdn,
            'iso/iso/manifests')
        utils.copy_tree(self.cfg['paths']['puppet_manifests'], path)

    def create(self):
        """generate the MD5 hashes and build the ISO"""
        utils.run('cd "%s" && md5sum $(find . \! -name "md5sum.txt" \! -path '
        '"./isolinux/*" -follow -type f) > md5sum.txt' % self.work_iso)
        utils.run('cd "%s" && mkisofs -quiet -o "%s" -r -J -no-emul-boot '
            '-boot-load-size 4 -boot-info-table -b isolinux/isolinux.bin -c '
            'isolinux/boot.cat iso' % (self.work_path, self.iso_dst))