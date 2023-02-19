import xml.etree.ElementTree as ET
import html

START = 't'
BLOCK_DURATION = 'd'
WORD_DURATION = 'ac'

def xml_to_srt(xml: str, max_len: int = 200) -> str:
    """
    Converts the passed xml into an SRT file
    
    Parameters
    ----------
    xml: str
        The xml to convert into an SRT file
    max_len: int
        The maximum length of the caption. Used to keep captions from wrapping
    """

    print(xml)
    tree = ET.fromstring(xml)

    output = ""
    caption_number = 1

    for child in list(tree[1]):
        frame_len = get_frame_len(child, max_len)
    
        start, end = None, None
        text = ""
        prev = ""
        start = get_start(child)
        for word in list(child):
            text += html.unescape(word.text)

            if not start:
                start = get_start(word)

            if len(text) > frame_len * caption_number: # Makes sure the overlap is not too much 
                # Saves the text
                output += out(caption_number, start, get_start(word) + int(word.attrib[WORD_DURATION]), text)
                start = None
                text = "" # Clears the text
                caption_number += 1

        if not text == "":
            # Also saves the text
            output += out(caption_number, start, get_end(word), text)
            caption_number += 1
    
    return output


# def xml_to_srt_bad(xml: str, empty=True) -> str: # Perfectly fine to push to the PyTube Repository
    # Creates the element tree
    tree = ET.fromstring(xml)

    output = ""
    caption_number = 0
    for i, child in enumerate(tree[1]):
        text = ""
        for word in list(child): # Children have a nested word by word structure which will just be ignored
            text += html.unescape(word.text)

        caption = text.replace("\n", " ").replace("  ", " ")
        try:
            duration = float(child.attrib["d"])
        except KeyError:
            duration = 0.0
        start = float(child.attrib["t"])
        end = start + duration

        if not empty and text == "": # Creates blank spaces which should probably make SRTs output correctly
            continue
        if text == "":
            text = "__"
        
        caption_number += 1
        output += f"{caption_number}\n" # Sequence number only outputs when text is actually there
        output += f"{fmt_time(start)} --> {fmt_time(end)}\n"
        output += f"{caption}\n\n"

    return output

def get_frame_len(child: str, max_len: int) -> int:
    """
    Gets the length of each frame
    """
    words = ""
    for word in list(child):
        words += html.unescape(word.text)
    
    frames = len(words) // max_len + 1
    return len(words) // frames


def get_start(word) -> int:
    """
    Gets the start time of the word
    """
    return int(word.attrib[START])


def get_end(word) -> int:
    """
    Gets the end time of the word
    """
    return int(word.attrib[START]) + int(word.attrib[WORD_DURATION])


def out(i, start, end, caption):
    """
    Formats the srt output
    """
    output = ""
    output += f"{i}\n" # Sequence number only outputs when text is actually there
    output += f"{fmt_time(start)} --> {fmt_time(end)}\n"
    output += f"{caption}\n\n"
    return output


def fmt_time(time: int) -> str:
    """
    Formats the time in miliseconds
    """
    return f"{int(time // 1000 // 60 // 60)}:{int(time // 1000 // 60 % 60)}:{int(time // 1000 % 60)},{int(time % 1000)}"