# pythesseract image recognition is not good enough for low resolution
# import pytesseract

from PIL import Image

from pathlib import Path
import config

IMAGE_PATH = Path(__file__).resolve().parents[2] / "media" / "NormalMode (121).png"
MANSION = [["" for _ in range(9)] for _ in range(5)]


def main():

    im = Image.open(IMAGE_PATH)
    for i in range(len(MANSION)):
        for j in range(len(MANSION[i])):
            start_x = config.BOX_START_X + ((i + 1) * config.ROOM_PIXEL_SIZE)
            start_y = config.BOX_START_Y + ((j + 1) * config.ROOM_PIXEL_SIZE)
            end_x = start_x + config.ROOM_PIXEL_SIZE
            end_y = start_y + config.ROOM_PIXEL_SIZE
            box = (start_x, start_y, end_x, end_y)

            cropped = im.crop(box)
            # print(pytesseract.image_to_string(cropped))
            cropped.show()


if __name__ == "__main__":
    main()
