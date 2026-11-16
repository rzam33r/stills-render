"""Which voice a plan gets, in one place.

Standard library only, on purpose: the film workflow reads this before it
installs anything, to decide which voice to install (Kokoro, Chatterbox or
Azure) and how many parts to record at once.

Hindi films are read by Chatterbox Multilingual's Hindi edition (MIT): on
15 Nov 2026 it was understood far better than Kokoro's Hindi on the same
script, and Roshan chose it on 16 Nov. English stays on Kokoro. A plan can
still name a Kokoro Hindi voice (hm_omega...) to use Kokoro.
(On 15 Nov 2026 that step imported voice.py, which needs numpy, and the first
film from the upload page's new tab stopped at "Voice recorded -- failed".)
"""
import re

DEFAULT_VOICE = {'en': 'am_michael', 'hi': 'chatterbox-hi'}
CHATTERBOX_VOICES = {'chatterbox-hi'}
HINDI_VOICES = {'chatterbox-hi', 'hm_omega', 'hm_psi', 'hf_alpha', 'hf_beta'}
KOKORO_VOICES = {'am_michael', 'am_adam', 'am_eric', 'am_liam', 'am_onyx', 'am_puck', 'am_fenrir',
                 'af_heart', 'af_bella', 'af_nicole', 'af_sarah', 'af_sky', 'af_nova', 'af_river',
                 'bm_george', 'bm_lewis', 'bm_daniel', 'bm_fable', 'bf_emma', 'bf_isabella', 'bf_alice', 'bf_lily',
                 'hm_omega', 'hm_psi', 'hf_alpha', 'hf_beta'}
AZURE = re.compile(r'^[a-z]{2}-[A-Z]{2}-[A-Za-z]+Neural$')


def is_azure(voice):
    return bool(AZURE.match(str(voice)))


def is_chatterbox(voice):
    return str(voice) in CHATTERBOX_VOICES


def is_hindi_voice(voice):
    return str(voice) in HINDI_VOICES or str(voice).startswith('hi-IN-')


# Chatterbox needs about 11 s of a GitHub computer per second of speech, and
# a step may run at most 6 hours, so a long Hindi film is recorded in parts at
# the same time, each about 12 minutes of speech (about 2.5 hours of work).
CHARS_PER_SECOND = 13.0          # Hindi narration, with its pauses
PART_SECONDS = 12 * 60
MAX_PARTS = 8


def voice_parts(plan, engine, forced=None):
    """How many parts the narration is recorded in at the same time."""
    if engine != 'chatterbox':
        return 1
    if forced:
        return max(1, min(MAX_PARTS, int(forced)))
    chars = sum(len(str(s.get('say', ''))) for s in plan.get('shots', []) if isinstance(s, dict))
    seconds = chars / CHARS_PER_SECOND
    return max(1, min(MAX_PARTS, -(-int(seconds) // PART_SECONDS)))


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
    if is_chatterbox(voice):
        return 'chatterbox', voice, ''
    if not is_azure(voice):
        return 'kokoro', voice, ''
    if azure_key_set:
        return 'azure', voice, ''
    lang = plan.get('language', 'en')
    fallback = DEFAULT_VOICE.get(lang, 'am_michael')
    engine = 'chatterbox' if is_chatterbox(fallback) else 'kokoro'
    return engine, fallback, (f'The plan asks for the Azure voice {voice}, but there is no AZURE_SPEECH_KEY '
                                f'secret, so this film uses the voice {fallback}. Update the ChatGPT '
                                'project files to stop seeing this.')
