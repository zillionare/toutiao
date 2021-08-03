"""Main module."""
import os

import sanic
from toutiao.client import ToutiaoClient

app = sanic.Sanic("toutiaoClient")


@app.route("/toutiao", methods=["GET"])
async def show_qr_img(request):
    """Show QR code."""
    qr_img = os.path.expanduser("~/toutiao/login_qr.png")
    return await sanic.response.file(
        qr_img,
        headers={
            "Content-Type": "image/png",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )


if __name__ == "__main__":
    tc = ToutiaoClient()
    app.register_listener(tc.start, event="before_server_start")
    app.run(host="0.0.0.0", port=3182, register_sys_signals=True, debug=True)
