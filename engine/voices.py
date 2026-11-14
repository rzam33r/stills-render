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
