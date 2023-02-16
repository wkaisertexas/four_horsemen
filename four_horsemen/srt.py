import xml.etree.ElementTree as ET
import html

def xml_to_srt(xml: str, max_len: int = 200) -> str: # TODO: Stop this from having overlapps
    """
    Converts the passed xml into an SRT file with a max length to keep everything on one line
    """

    print(xml)
    tree = ET.fromstring(xml)

    output = ""
    j = 1

    for child in list(tree[1]):
        words = ""
        for word in list(child):
            words += html.unescape(word.text)

        frames = len(words) // max_len + 1
        frame_len = len(words) // frames

        start, end = None, None

        text = ""
        k = 1

        prev = ""
        start = int(child.get('t'))
        for word in list(child):
            text += html.unescape(word.text)

            if not start:
                start = int(word.attrib['t'])

            if len(text) > frame_len * k: # Makes sure the overlap is not too much 
                # Saves the text
                output += out(j, start, int(word.attrib['t']) + int(word.attrib['ac']), text)
                start = None
                text = "" # Clears the text
                j += 1
                k += 1 

        if not text == "":
            # Also saves the text
            output += out(j, start, int(child.attrib['t']) + int(child.attrib['d']), text)
            j += 1
            k += 1
    
    return output

def xml_to_srt_bad(xml: str, empty=True) -> str: # Perfectly fine to push to the PyTube Repository
    # Creates the element tree
    tree = ET.fromstring(xml)

    output = ""
    j = 0
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
        
        j += 1
        output += f"{j}\n" # Sequence number only outputs when text is actually there
        output += f"{fmt_time(start)} --> {fmt_time(end)}\n"
        output += f"{caption}\n\n"

    return output

def out(i, start, end, caption):
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