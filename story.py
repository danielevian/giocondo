import os
import json
import replicate
import streamlit as st
from dotenv import load_dotenv
from elevenlabs import generate#, play
from langchain.prompts import (
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    HumanMessage,
    SystemMessage,
    AIMessage
)
#from langchain.chains import LLMChain
#from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from prompt import PROMPT_SYSTEM_ZERO, PROMPT_USER_ZERO



load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
eleven_api_key = os.getenv("ELEVEN_API_KEY")

OPTION_1_TEMPLATE = "\nUSER: Continue with Option 1.\n Please answer in JSON format.\n"
OPTION_2_TEMPLATE = "\nUSER: Continue with Option 2.\n Please answer in JSON format.\n"

CHARACTER_IMAGE_DESCR = {
    "jocondo": " (funny wizard human mouse male 7 years old) ",
    "hermione": " (beautiful human mouse female 7 years old) ",
    "earnest": " (funny human pigeon male 7 years old) ",
    "emma": " (beautiful 7 years old girl) ",
    "dumbledore": " (old sage wizard human mouse) ",
    "hagrid": " ( long bearded, chubby mid aged human with bratty gaze) "
}

chat = ChatOpenAI(temperature=0.9, model_name="gpt-3.5-turbo")

# chat messages are in session state

if 'chat' not in st.session_state:
    st.session_state['chat'] = []

def append_human_to_session(message):
    st.session_state['chat'].append(HumanMessage(content = message))

def append_system_to_session(message):
    st.session_state['chat'].append(SystemMessage(content = message))

def append_ai_to_session(message):
    st.session_state['chat'].append(AIMessage(content = message))

if 'chat' in st.session_state and len(st.session_state['chat']) == 0:
    append_system_to_session(PROMPT_SYSTEM_ZERO)


## how do I use "memory" per langchain?? It's REALLY confused in documentation


def generate_story():
    reply = chat(st.session_state['chat'])
    return reply.content

# da provare anche https://play.ht/ultra-realistic-voices/
def generate_audio(text, voice):
    """Convert the generated story to audio using the Eleven Labs API."""
    audio = generate(text=text, voice=voice, api_key=eleven_api_key)
    return audio

def generate_images(story_text):
    """Generate images using the story text using the Replicate API."""
    #story_prompt = story_text.lower()
    #for key in CHARACTER_IMAGE_DESCR.keys():
    #   story_prompt = story_prompt.replace(key, CHARACTER_IMAGE_DESCR[key])
    print("IMAGE INPUT:")
    print(story_text + " All characters are humans with mouse ears, digital painting, cartoon, in the style of Studio Ghibli, detailed, wizards, dressed, cute and quirky, fantasy art, bokeh, hand-drawn, digital painting, bird's-eye view, retro aesthetic",)
    output = replicate.run(
        "stability-ai/stable-diffusion:db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5bf",
        input={
            "prompt": story_text + " All characters are humans with mouse ears, digital painting, cartoon, in the style of Studio Ghibli, detailed, furry, wizards, dressed, cute and quirky, fantasy art, bokeh, hand-drawn, digital painting, bird's-eye view, retro aesthetic",
            "negative_prompt": "distorted, ugly, deformed",
            "guidance_scale": 7
            }
    )
    return output


def app():
    #print("____________")
    #print("\n".join([x.content for x in st.session_state['chat']]))
    #print("____________")

    st.title("Giocondo time!")

    body_container = st.container()
    options_container = st.container()

    with body_container:
        st.write("Hi there! This is Giocondo Story maker.\nEnter a title and hit submit to start a new story!")
        title_text = st.text_input(
            "Title",
            max_chars=None,
            type="default",
            placeholder="Enter the title of the story",
        )

    if title_text:
        # first time, append it to chat messages. In session I have only the system prompt.
        if len(st.session_state['chat']) <= 1:
            append_human_to_session(PROMPT_USER_ZERO.format(magic_words = title_text))

        with options_container:
            opt1 = st.button("option 1")
            opt2 = st.button("option 2")
            if opt1:
                append_human_to_session(OPTION_1_TEMPLATE)
            elif opt2:
                append_human_to_session(OPTION_2_TEMPLATE)

        with body_container:
            with st.spinner("waiting on storyteller in chief..."):
                #print(">> generating with " + str(len(st.session_state['chat'])) + " messages - " + st.session_state['chat'][-1].content + " as last message.")
                _story = generate_story()
                print(_story)
                story_json = json.loads(_story)
                
                if story_json:
                    append_ai_to_session(story_json['story'])# in memory
                    print(st.session_state['chat'])

                    for line in st.session_state['chat'][2:]:
                        if line.content == OPTION_1_TEMPLATE:
                            st.write("You chose option 1.")
                        elif line.content == OPTION_2_TEMPLATE:
                            st.write("You chose option 2.")
                        else:
                            st.write(line.content)
                        st.divider()

                    # now the image
                    with st.spinner("Waiting for image..."):
                        print("Now the image...")
                        image = generate_images(story_json['image_summary'])
                        print("DONE!")
                        if image:
                            st.image(image)
                

if __name__ == '__main__':
    app()

