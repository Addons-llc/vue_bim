import { onBeforeUnmount, ref } from 'vue'

const VOICE_ERROR_MESSAGES = {
  'audio-capture': 'No microphone was found on this device.',
  network: 'Voice search needs an internet connection. Please try again.',
  'no-speech': "We didn't catch that. Please try again.",
  'not-allowed': 'Microphone access is blocked. Allow it in your browser settings to use voice search.',
  'service-not-allowed': 'Microphone access is blocked. Allow it in your browser settings to use voice search.',
}
const DEFAULT_VOICE_ERROR = 'Voice search is not working right now. Please try again.'

export function useVoiceSearch(onResult) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  const isVoiceSupported = Boolean(SpeechRecognition)
  const isListening = ref(false)
  const voiceTranscript = ref('')
  const voiceError = ref('')
  let recognition = null

  function finishListening() {
    const transcript = voiceTranscript.value.trim().replace(/[.?!]+$/, '')

    recognition = null
    isListening.value = false

    if (voiceError.value) {
      return
    }

    if (transcript) {
      onResult(transcript)
      return
    }

    voiceError.value = VOICE_ERROR_MESSAGES['no-speech']
  }

  function startListening() {
    if (!isVoiceSupported || isListening.value) {
      return
    }

    const activeRecognition = new SpeechRecognition()

    recognition = activeRecognition
    voiceTranscript.value = ''
    voiceError.value = ''
    // Product names are in English, so a device set to another language should still match them.
    activeRecognition.lang = 'en-US'
    activeRecognition.interimResults = true
    activeRecognition.maxAlternatives = 1

    activeRecognition.onresult = (event) => {
      const results = Array.from(event.results)

      voiceTranscript.value = results.map((result) => result[0].transcript).join('')

      if (results.every((result) => result.isFinal)) {
        activeRecognition.stop()
      }
    }

    activeRecognition.onerror = (event) => {
      if (event.error !== 'aborted') {
        voiceError.value = VOICE_ERROR_MESSAGES[event.error] || DEFAULT_VOICE_ERROR
      }
    }

    // A cancelled session has already been replaced, so its late end event is ignored.
    activeRecognition.onend = () => {
      if (recognition === activeRecognition) {
        finishListening()
      }
    }

    try {
      activeRecognition.start()
      isListening.value = true
    } catch {
      recognition = null
      voiceError.value = DEFAULT_VOICE_ERROR
    }
  }

  function cancelListening() {
    const activeRecognition = recognition

    recognition = null
    isListening.value = false
    activeRecognition?.abort()
  }

  onBeforeUnmount(cancelListening)

  return {
    cancelListening,
    isListening,
    isVoiceSupported,
    startListening,
    voiceError,
    voiceTranscript,
  }
}
