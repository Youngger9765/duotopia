/**
 * Example Component: How to use Azure Speech Service for Pronunciation Analysis
 *
 * This component demonstrates the recommended pattern for integrating
 * Azure Speech Service with the AudioRecorder component.
 *
 * Key Benefits:
 * - Direct Azure SDK calls (no backend proxy) - 56% faster
 * - Automatic token caching (9 minutes)
 * - Background upload for analytics (non-blocking)
 * - Automatic retry on token expiration
 */

import AudioRecorder from "@/components/shared/AudioRecorder";
import { useAzurePronunciation } from "@/hooks/useAzurePronunciation";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface PronunciationResult {
  pronunciationScore: number;
  accuracyScore: number;
  fluencyScore: number;
  completenessScore: number;
  words?: Array<{
    word: string;
    accuracyScore: number;
    errorType: string;
  }>;
}

interface Props {
  referenceText: string;
  onAnalysisComplete?: (result: PronunciationResult) => void;
}

export default function AzurePronunciationExample({
  referenceText,
  onAnalysisComplete,
}: Props) {
  const { isAnalyzing, result, error, analyzePronunciation } =
    useAzurePronunciation();

  const handleRecordingComplete = async (blob: Blob) => {
    // Immediately analyze pronunciation using Azure Speech
    const analysisResult = await analyzePronunciation(blob, referenceText);

    if (analysisResult && onAnalysisComplete) {
      onAnalysisComplete(analysisResult);
    }
  };

  return (
    <div className="space-y-4">
      {/* Reference Text Display */}
      <Card className="p-4 bg-blue-50">
        <h3 className="font-medium mb-2">Reference Text:</h3>
        <p className="text-lg">{referenceText}</p>
      </Card>

      {/* Audio Recorder */}
      <AudioRecorder
        title="Record Your Pronunciation"
        description="Read the reference text above and record your pronunciation"
        onRecordingComplete={handleRecordingComplete}
        disabled={isAnalyzing}
      />

      {/* Analysis Status */}
      {isAnalyzing && (
        <Card className="p-4 bg-yellow-50">
          <p className="text-center">
            Analyzing pronunciation with Azure Speech...
          </p>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <Card className="p-4 bg-red-50 border-red-200">
          <p className="text-red-600">{error}</p>
        </Card>
      )}

      {/* Results Display */}
      {result && (
        <Card className="p-4">
          <h3 className="font-medium mb-3">Pronunciation Analysis Results</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <span className="text-sm text-gray-600">
                Pronunciation Score:
              </span>
              <Badge
                variant={
                  result.pronunciationScore >= 80 ? "default" : "destructive"
                }
              >
                {result.pronunciationScore.toFixed(1)}
              </Badge>
            </div>
            <div>
              <span className="text-sm text-gray-600">Accuracy:</span>
              <Badge>{result.accuracyScore.toFixed(1)}</Badge>
            </div>
            <div>
              <span className="text-sm text-gray-600">Fluency:</span>
              <Badge>{result.fluencyScore.toFixed(1)}</Badge>
            </div>
            <div>
              <span className="text-sm text-gray-600">Completeness:</span>
              <Badge>{result.completenessScore.toFixed(1)}</Badge>
            </div>
          </div>

          {/* Word-level feedback */}
          {result.words && result.words.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium mb-2">Word-level Analysis:</h4>
              <div className="flex flex-wrap gap-2">
                {result.words.map((word, idx) => (
                  <Badge
                    key={idx}
                    variant={
                      word.errorType === "None" ? "default" : "destructive"
                    }
                  >
                    {word.word} ({word.accuracyScore.toFixed(0)})
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
