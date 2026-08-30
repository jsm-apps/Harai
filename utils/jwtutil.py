import jwt


def decode_jwt(token):
    try:
        header = jwt.get_unverified_header(token)

        payload = jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": False,
            }
        )

        return {
            "header": header,
            "payload": payload,
        }

    except Exception as e:
        return {
            "error": str(e)
        }