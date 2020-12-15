def check_jpg_jpeg(path):
    with open(path, "rb") as f:
        f.seek(-2, 2)#set the position to the end of file and move back for 2 charactors
        img_text = f.read()#only read 2 charactors at the end of file
    """检测jpg图片完整性，完整返回True，不完整返回False"""
    return img_text.endswith(b'\xff\xd9')


def check_png(path):
    with open(path, "rb") as f:
        f.seek(-2, 2)#set the position to the end of file and move back for 2 charactors
        img_text = f.read()#only read 2 charactors at the end of file
    """检测png图片完整性，完整返回True，不完整返回False"""
    return img_text.endswith(b'\xaeB`\x82')


def check_jpg_jpeg_stream(bytestream:bytes):
    return bytestream.endswith(b'\xff\xd9')


def check_png_stream(bytestream:bytes):
    return bytestream.endswith(b'\xaeB`\x82')
