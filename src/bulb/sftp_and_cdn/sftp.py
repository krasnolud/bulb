from bulb.sftp_and_cdn.cdn_apis import CDN77
from bulb.sftp_and_cdn.exceptions import *
from django.conf import settings
from base64 import decodebytes
import warnings
import paramiko
import pysftp
import os

BASE_DIR = os.environ["BASE_DIR"]


class SFTP:

    @staticmethod
    def connect(log=None):

        keydata = settings.BULB_SFTP_HOST_SSH_KEY

        if keydata is None:
            raise BULBHostSSHKeyError("To establish an SFTP connection you have to provide the SSH key of the server. Please put it in the BULB_SFTP_HOST_SSH_KEY variable in 'settings.py'.")

        else:
            key = paramiko.RSAKey(data=decodebytes(keydata))

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=UserWarning)
                cnopts = pysftp.CnOpts()
                cnopts.hostkeys.add(settings.BULB_SFTP_HOST, 'ssh-rsa', key)

            return pysftp.Connection(host=settings.BULB_SFTP_HOST, username=settings.BULB_SFTP_USER, password=settings.BULB_SFTP_PASSWORD, cnopts=cnopts, log=log)

    @staticmethod
    def push_src_staticfiles(src_type, local_staticfiles_folder_path):
        """
        This method post new source staticfiles on the SFTP server.

        :param (required) src_type: The type of source staticfiles to post on the sftp. "src" / "bundled"
        :param (required) local_staticfiles_folder_path: The local staticfiles folder path.
        :return:
        """
        if src_type == "raw":
            sftp_staticfiles_folder_path = "/www/staticfiles/raw_src"

        elif src_type == "bundled":
            sftp_staticfiles_folder_path = "/www/staticfiles/bundled_src"

        else:
            raise BULBStaticfilesError(
                f'The "src_type" parameter of the clear_staticfiles() method should be "raw" or "bundled". It is {str(src_type)}.')

        with SFTP.connect() as sftp:

            print("\n------------------------------------------" + ("---" if src_type == "raw" else "-------"))
            print(f"--  UPLOAD NEW {src_type.upper()} SRC STATICFILES ON SFTP --")
            print(("---" if src_type == "raw" else "-------") + "------------------------------------------\n")

            print("\nThis operation could take few minutes (it depends of the number and the weight of your static files)...\n")

            try:
                sftp.put_r(local_staticfiles_folder_path, sftp_staticfiles_folder_path)

            # Check and create default storage folders if they are not already created.
            except FileNotFoundError:
                if not sftp.exists("/www/staticfiles"):
                    sftp.mkdir("/www/staticfiles")

                if not sftp.exists(f"/www/staticfiles/{src_type}_src"):
                    sftp.mkdir(f"/www/staticfiles/{src_type}_src")

                sftp.put_r(local_staticfiles_folder_path, sftp_staticfiles_folder_path)

            finally:
                print("Done ✔\n")


    @staticmethod
    def clear_src_staticfiles(src_type):
        """
        This method delete old source staticfiles on the SFTP server.

        :param (required) src_type: The type(s) of source staticfiles to remove. "src" / "bundled"
        :return:
        """
        if src_type == "raw":
            sftp_staticfiles_folder_path = "/www/staticfiles/raw_src"

        elif src_type == "bundled":
            sftp_staticfiles_folder_path = "/www/staticfiles/bundled_src"

        else:
            raise BULBStaticfilesError(f'The "src_type" parameter of the clear_staticfiles() method should be "raw", "bundled". It is {str(src_type)}.')

        with SFTP.connect() as sftp:

            files_to_purge_list = []

            def remove_file(path):
                if sftp.isfile(path):
                    rectified_path = "".join([x for x in path][4:])  # Delete '/www' on the path
                    files_to_purge_list.append(rectified_path)

                    sftp.remove(path)
                    print("'" + path + "'", " removed.")

            paths_list = []

            def add_to_paths_list(x):
                paths_list.append(x)

            print(f"\n-----------------------------------------{'----' if src_type == 'bundled' else ''}")
            print(f"--  REMOVE OLD {src_type.upper()} SRC FILES FROM SFTP --")
            print(f"-----------------------------------------{'----' if src_type == 'bundled' else ''}\n")

            try:
                sftp.walktree(sftp_staticfiles_folder_path, fcallback=remove_file, dcallback=remove_file, ucallback=remove_file)

            except FileNotFoundError:
                print(f"\n      There were no {src_type} source files to remove on the sftp.\n")

            print(f"\n-----------------------------------------------{'----' if src_type == 'bundled' else ''}")
            print(f"--  REMOVE OLD {src_type.upper()} SRC DIRECTORIES FROM SFTP --")
            print(f"-----------------------------------------------{'----' if src_type == 'bundled' else ''}\n")

            try:
                sftp.walktree(sftp_staticfiles_folder_path, fcallback=add_to_paths_list, dcallback=add_to_paths_list, ucallback=add_to_paths_list)

            except FileNotFoundError:
                print(f"\n      There were no {src_type} source directories to remove on the sftp.\n")

            else:
                while paths_list:
                    for path in paths_list:
                        try:
                            sftp.rmdir(path)
                            pass

                        except :
                            continue

                        else:
                            print(path, " removed !")
                            paths_list.remove(path)

            if settings.BULB_USE_CDN77:
                print(f"\n----------------------------------------------{'----' if src_type == 'bundled' else ''}")
                print(f"--  PURGE {src_type.upper()} STATICFILES ON CDN77 SERVERS  --")
                print(f"----------------------------------------------{'----' if src_type == 'bundled' else ''}\n")

                files_to_purge_number = len(files_to_purge_list)

                print(f"\n      {files_to_purge_number} file{'s' if files_to_purge_number > 1 or files_to_purge_number == 0 else ''} to purge.\n")

                # CDN77 allows up to 20 requests with up to 2000 files to purge every 5 minutes.
                # See : https://client.cdn77.com/support/api/version/2.0/data

                if files_to_purge_number != 0:

                    # If the number of files to purge is under the limit send a unique request:
                    if files_to_purge_number < 2000:
                        CDN77.purge(files_to_purge_list)

                    # Else send multiple requests, each with up to 2000 files maximum.
                    else:
                        request_number = 1

                        while files_to_purge_number >= 2000:
                            purge_response = CDN77.purge(files_to_purge_list[:2000], request_number)

                            request_number += 1
                            files_to_purge_number -= 2000
                            files_to_purge_list = files_to_purge_list[2000:]

                            if purge_response.status_code != "200":
                                break

                        if files_to_purge_number > 0:
                            CDN77.purge(files_to_purge_list, request_number)