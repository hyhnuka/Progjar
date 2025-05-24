import os
import json
import base64
from glob import glob

class FileInterface:
    def __init__(self):
        # Pastikan kita berada di folder 'files'
        os.chdir('files/')

    def list(self, params=[]):
        try:
            filelist = glob('*.*')
            return dict(status='OK', data=filelist)
        except Exception as e:
            return dict(status='ERROR', data=str(e))

    def get(self, params=[]):
        try:
            filename = params[0] if params else ''
            if filename == '':
                return dict(status='ERROR', data='parameter tidak lengkap')
            with open(filename, 'rb') as fp:
                isifile = base64.b64encode(fp.read()).decode()
            return dict(status='OK', data_namafile=filename, data_file=isifile)
        except Exception as e:
            return dict(status='ERROR', data=str(e))

    def upload(self, params=[]):
        """
        upload <nama_file> <content_base64>
        """
        try:
            if len(params) < 2:
                return dict(status='ERROR', data='parameter tidak lengkap')
            filename, filedata_b64 = params[0], params[1]
            with open(filename, 'wb') as fp:
                fp.write(base64.b64decode(filedata_b64))
            return dict(status='OK', data=f'file "{filename}" berhasil diupload')
        except Exception as e:
            return dict(status='ERROR', data=str(e))

    def delete(self, params=[]):
        """
        delete <nama_file>
        """
        try:
            filename = params[0] if params else ''
            if filename == '':
                return dict(status='ERROR', data='parameter tidak lengkap')
            os.remove(filename)
            return dict(status='OK', data=f'file "{filename}" berhasil dihapus')
        except Exception as e:
            return dict(status='ERROR', data=str(e))


if __name__ == '__main__':
    f = FileInterface()
    print(f.list())
    print(f.get(['pokijan.jpg']))