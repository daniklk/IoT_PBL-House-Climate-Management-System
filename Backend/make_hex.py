def generate_ir_signal(protocol, device, subdevice, function) -> dict[str, str, bool]:
    """
    Uses encodeir binary to generate IR signal
    :param protocol:
    :param device:
    :param subdevice:
    :param function:
    :return:
    """
    import subprocess
    import platform

    try:
        system = platform.system()
        if system == "Windows":
            path_encodeir = "bin/windows/encodeir.exe"
        elif system == "Darwin":
            path_encodeir = "bin/macos/encodeir"
        else:
            path_encodeir = "bin/linux/encodeir"

        args = [protocol, device, subdevice, function]
        result = subprocess.run(
            [path_encodeir] + args,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return {
                'success': True,
                'output': result.stdout.replace(" ", "").strip(),
                'command': f"{path_encodeir} {' '.join(args)}"
            }
        else:
            return {
                'success': False,
                'error': result.stderr.strip() or f"Process failed with return code {result.returncode}",
                'command': f"{path_encodeir} {' '.join(args)}"
            }

    except FileNotFoundError:
        return {
            'success': False,
            'error': f'encodeir binary not found at {path_encodeir}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
