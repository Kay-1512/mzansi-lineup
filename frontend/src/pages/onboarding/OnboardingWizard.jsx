import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import StepArtists from "./StepArtists";
import StepCity from "./StepCity";
import StepGenres from "./StepGenres";
import StepSources from "./StepSources";

const STEPS = ["Sources", "Genres", "Artists", "City"];

export default function OnboardingWizard() {
  const [step, setStep] = useState(0);
  const navigate = useNavigate();
  const { refreshProfile } = useAuth();

  async function finish() {
    await refreshProfile();
    navigate("/");
  }

  return (
    <div className="onboarding-page">
      <div className="onboarding-progress">
        {STEPS.map((label, i) => (
          <div key={label} className={`progress-dot ${i <= step ? "active" : ""}`}>
            <span>{i + 1}</span>
            <small>{label}</small>
          </div>
        ))}
      </div>

      {step === 0 && <StepSources onNext={() => setStep(1)} />}
      {step === 1 && <StepGenres onNext={() => setStep(2)} onBack={() => setStep(0)} />}
      {step === 2 && <StepArtists onNext={() => setStep(3)} onBack={() => setStep(1)} />}
      {step === 3 && <StepCity onFinish={finish} onBack={() => setStep(2)} />}
    </div>
  );
}
