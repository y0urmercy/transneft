import { Volume2, Square } from "lucide-react";
import { useSpeech } from "../../hooks/useSpeech";

const VoiceOutput = ({ text }) => {
  const { speak, stop, isSpeaking } = useSpeech();

  const handleSpeak = () => {
    if (isSpeaking) {
      stop();
    } else {
      speak(text);
    }
  };

  return (
    <button
      onClick={handleSpeak}
      disabled={!text}
      className={`p-2 rounded ${
        isSpeaking ? "bg-red-500" : "bg-green-500"
      } text-white disabled:bg-gray-300`}
    >
      {isSpeaking ? <Square size={16} /> : <Volume2 size={16} />}
    </button>
  );
};

export default VoiceOutput;
