import logging
import re

from tplinkrouterc6u import TPLinkMRClient

_logger = logging.getLogger()
_logger.setLevel(logging.DEBUG)


class CustomTPLinkMRClient(TPLinkMRClient):
    @staticmethod
    def _merge_response(response: str) -> dict:
        result = {}
        obj = {}
        lines = response.split("\n")

        for line in lines:
            if line.startswith("["):
                regexp = re.search(r"\[\d,\d,\d,\d,\d,\d\](\d)", line)
                if regexp is not None:
                    obj = {}
                    index = regexp.group(1)
                    item = result.get(index)
                    if item is not None:
                        if item.__class__ != list:
                            result[index] = [item]
                        result[index].append(obj)
                    else:
                        result[index] = obj
                continue

            if "=" in line:
                keyval = line.split("=")

                # removed line, gave bugs
                # assert len(keyval) == 2

                obj[keyval[0]] = keyval[1]

        return result if result else []


_logger.info("starting program...")

router = None

try:

    router = CustomTPLinkMRClient("http://<IP-ADDRESS>", "<PASSWORD>")

    _logger.debug("authorizing...")

    router.authorize()  # authorizing

    _logger.debug("authorized...")

    firmware = router.get_firmware()
    _logger.debug("firmware of router retrieved: %s", firmware)

    status = router.get_status()
    _logger.debug("status of router retrieved: %s", status)

    if status.conn_type == "LTE":
        lte_status = router.get_lte_status()

        _logger.debug("LTE status of router: %s", lte_status)

        if lte_status.sms_unread_count > 0:

            _logger.info("unread sms found, parsing unread smses...", lte_status)

            smses = router.get_sms()

            for sms in smses:
                if sms.unread == True and "Je hebt 80%" in sms.content:
                    _logger.info(
                        "unread limit sms found, sending sms to request more bandwidth...",
                        lte_status,
                    )

                    router.set_sms_read(sms)
                    router.send_sms("1280", "EXTRA")
        else:

            _logger.info("no unread sms...", lte_status)
except Exception as err:
    _logger.exception("error occured during reading sms", err)
finally:
    _logger.debug("logging out")
    if router:
        router.logout()
