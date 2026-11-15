"""Which voice a plan gets, in one place.

Standard library only, on purpose: the film workflow reads this before it
installs anything, to decide whether to install Kokoro or the Azure voice.
(On 15 Nov 2026 that step imported voice.py, which needs numpy, and the first
film from the upload page's new tab stopped at "Voice recorded -- failed".)
"""
import re

DEFAULT_VOICE = {'en': 'am_michael', 'hi': 'hm_omega'}
KOKORO_VOICES = {'am_michael', 'am_adam', 'am_eric', 'am_liam', 'am_onyx', 'am_puck', 'am_fenrir',
                 'af_heart', 'af_bella', 'af_nicole', 'af_sarah', 'af_sky', 'af_nova', 'af_river',
                 'bm_george', 'bm_lewis', 'bm_daniel', 'bm_fable', 'bf_emma', 'bf_isabella', 'bf_alice', 'bf_lily',
                 'hm_omega', 'hm_psi', 'hf_alpha', 'hf_beta'}
AZURE = re.compile(r'^[a-z]{2}-[A-Z]{2}-[A-Za-z]+Neural$')


def is_azure(voice):
    return bool(AZURE.match(str(voice)))


def chosen_voice(plan):
    """The voice the film will use: the plan's own, or the language's default."""
    return plan.get('voice') or DEFAULT_VOICE.get(plan.get('language', 'en'), 'am_michael')


def voice_engine(plan, azure_key_set):
    """(engine, voice, warning) for a film.

    An Azure voice needs the AZURE_SPEECH_KEY secret. Without it the film
    takes Kokoro's voice for its language instead of stopping at the voice
    step, and the warning says so on the run page. (On 15 Nov 2026 an old
    copy of the ChatGPT pack still wrote "hi-IN-MadhurNeural"; this account
    has no Azure key.)
    """
    voice = chosen_voice(plan)
    if not is_azure(voice):
        return 'kokoro', voice, ''
    if azure_key_set:
        return 'azure', voice, ''
    lang = plan.get('language', 'en')
    fallback = DEFAULT_VOICE.get(lang, 'am_michael')
    return 'kokoro', fallback, (f'The plan asks for the Azure voice {voice}, but there is no AZURE_SPEECH_KEY '
                                f'secret, so this film uses the Kokoro voice {fallback}. Update the ChatGPT '
                                'project files to stop seeing this.')
