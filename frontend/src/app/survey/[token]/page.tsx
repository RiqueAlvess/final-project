"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { CheckCircle2, XCircle, AlertCircle, ChevronRight, ChevronLeft, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { surveyApi, SurveyData } from "@/services/campaigns";

// ── Scale labels ──────────────────────────────────────────────────────────────
const SCALE = [
  { value: 0, label: "Nunca" },
  { value: 1, label: "Raramente" },
  { value: 2, label: "Às vezes" },
  { value: 3, label: "Frequentemente" },
  { value: 4, label: "Sempre" },
];

const GENDER_OPTIONS = [
  { value: "M", label: "Masculino" },
  { value: "F", label: "Feminino" },
  { value: "O", label: "Outro" },
  { value: "P", label: "Prefiro não dizer" },
];

const AGE_OPTIONS = [
  { value: "UP_TO_25", label: "Até 25 anos" },
  { value: "26_35", label: "26–35 anos" },
  { value: "36_45", label: "36–45 anos" },
  { value: "46_55", label: "46–55 anos" },
  { value: "ABOVE_55", label: "Acima de 55 anos" },
  { value: "PREF", label: "Prefiro não dizer" },
];

type Step = "loading" | "error" | "consent" | "demographics" | "questions" | "done" | "already_answered";

// ── LGPD Consent Term ─────────────────────────────────────────────────────────
function ConsentTerm({
  campaignName,
  onAccept,
  onDecline,
}: {
  campaignName: string;
  onAccept: () => void;
  onDecline: () => void;
}) {
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle2 className="w-8 h-8 text-purple-600" />
        </div>
        <h1 className="text-2xl font-bold text-slate-900">
          Pesquisa de Clima Organizacional
        </h1>
        <p className="text-slate-500 mt-1">{campaignName}</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4 text-sm text-slate-700 leading-relaxed max-h-96 overflow-y-auto">
        <h2 className="font-bold text-base text-slate-900">
          Termo de Consentimento para Tratamento de Dados – Pesquisa de Clima
          Organizacional
        </h2>
        <p>
          Este documento visa registrar a manifestação livre, informada e inequívoca
          pela qual o Titular concorda com o tratamento de seus dados pessoais para
          uma finalidade específica, em estrita conformidade com a Lei Geral de
          Proteção de Dados Pessoais (Lei nº 13.709/2018 - LGPD).
        </p>
        <div className="space-y-3">
          <div>
            <h3 className="font-semibold text-slate-900">1. Objetivo da Coleta</h3>
            <p>
              A presente pesquisa, realizada por meio da plataforma Vivamente360, tem
              como objetivo avaliar o clima organizacional e mapear fatores
              psicossociais no ambiente de trabalho. As informações coletadas servirão
              exclusivamente para embasar diagnósticos e desenvolver ações de melhoria
              contínua voltadas ao bem-estar, saúde e engajamento dos colaboradores.
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-slate-900">2. Dados Coletados</h3>
            <p>
              Para a realização da pesquisa poderão ser tratados dados demográficos e
              percepções relacionadas ao ambiente de trabalho.
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-slate-900">
              3. Tratamento e Anonimização
            </h3>
            <p>
              Os relatórios serão apresentados apenas de forma agregada e anonimizada.
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-slate-900">
              4. Armazenamento e Segurança
            </h3>
            <p>
              Os dados serão armazenados em ambientes seguros com controle de acesso
              restrito.
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-slate-900">5. Direitos do Titular</h3>
            <p>
              O titular poderá solicitar acesso, correção ou eliminação dos dados
              conforme a LGPD.
            </p>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <Button
          className="w-full bg-purple-600 hover:bg-purple-700 h-12 text-base"
          onClick={onAccept}
        >
          <CheckCircle2 className="w-5 h-5 mr-2" />
          Li e concordo – Iniciar pesquisa
        </Button>
        <Button
          variant="outline"
          className="w-full h-12 text-slate-500"
          onClick={onDecline}
        >
          <XCircle className="w-4 h-4 mr-2" />
          Não concordo
        </Button>
      </div>
    </div>
  );
}

// ── Demographics ──────────────────────────────────────────────────────────────
function DemographicsStep({
  gender,
  ageRange,
  onGenderChange,
  onAgeRangeChange,
  onNext,
}: {
  gender: string;
  ageRange: string;
  onGenderChange: (v: string) => void;
  onAgeRangeChange: (v: string) => void;
  onNext: () => void;
}) {
  return (
    <div className="max-w-xl mx-auto space-y-6">
      <div className="text-center">
        <h2 className="text-xl font-bold text-slate-900">Dados Demográficos</h2>
        <p className="text-slate-500 text-sm mt-1">
          Opcional – suas respostas são anônimas
        </p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-6">
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-3">
            Gênero (opcional)
          </label>
          <div className="grid grid-cols-2 gap-2">
            {GENDER_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => onGenderChange(gender === opt.value ? "" : opt.value)}
                className={`px-4 py-2.5 rounded-lg border text-sm font-medium transition-all
                  ${
                    gender === opt.value
                      ? "border-purple-500 bg-purple-50 text-purple-700"
                      : "border-slate-200 text-slate-600 hover:border-slate-300"
                  }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-3">
            Faixa Etária (opcional)
          </label>
          <div className="grid grid-cols-2 gap-2">
            {AGE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() =>
                  onAgeRangeChange(ageRange === opt.value ? "" : opt.value)
                }
                className={`px-4 py-2.5 rounded-lg border text-sm font-medium transition-all
                  ${
                    ageRange === opt.value
                      ? "border-purple-500 bg-purple-50 text-purple-700"
                      : "border-slate-200 text-slate-600 hover:border-slate-300"
                  }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <Button
        className="w-full bg-purple-600 hover:bg-purple-700 h-12"
        onClick={onNext}
      >
        Continuar
        <ChevronRight className="w-4 h-4 ml-2" />
      </Button>
    </div>
  );
}

// ── Questions ─────────────────────────────────────────────────────────────────
function QuestionsStep({
  surveyData,
  answers,
  onAnswer,
  onBack,
  onSubmit,
  submitting,
}: {
  surveyData: SurveyData;
  answers: Record<number, number>;
  onAnswer: (questionId: number, value: number) => void;
  onBack: () => void;
  onSubmit: () => void;
  submitting: boolean;
}) {
  const allQuestions = surveyData.dimensions.flatMap((d) => d.questions);
  const answered = Object.keys(answers).length;
  const total = allQuestions.length;
  const progress = Math.round((answered / total) * 100);

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Progress */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex justify-between text-sm text-slate-600 mb-2">
          <span>Progresso</span>
          <span>
            {answered}/{total} respondidas
          </span>
        </div>
        <div className="h-2 bg-slate-100 rounded-full">
          <div
            className="h-full bg-purple-500 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Dimensions */}
      {surveyData.dimensions.map((dim) => (
        <div key={dim.id} className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 bg-slate-50 border-b border-slate-200">
            <h3 className="font-semibold text-slate-900">{dim.name}</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {dim.questions.length} perguntas
            </p>
          </div>
          <div className="divide-y divide-slate-100">
            {dim.questions.map((q, idx) => (
              <div key={q.id} className="px-6 py-4 space-y-3">
                <p className="text-sm text-slate-800 font-medium">
                  <span className="text-slate-400 text-xs mr-2">
                    {idx + 1}.
                  </span>
                  {q.text}
                </p>
                <div className="flex flex-wrap gap-2">
                  {SCALE.map((s) => (
                    <button
                      key={s.value}
                      onClick={() => onAnswer(q.id, s.value)}
                      className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-all
                        ${
                          answers[q.id] === s.value
                            ? "border-purple-500 bg-purple-600 text-white"
                            : "border-slate-200 text-slate-600 hover:border-purple-300 hover:bg-purple-50"
                        }`}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Submit */}
      <div className="flex gap-3 pb-6">
        <Button variant="outline" className="flex-1 h-12" onClick={onBack}>
          <ChevronLeft className="w-4 h-4 mr-2" />
          Voltar
        </Button>
        <Button
          className="flex-1 h-12 bg-purple-600 hover:bg-purple-700"
          onClick={onSubmit}
          disabled={answered < total || submitting}
        >
          {submitting ? (
            "Enviando..."
          ) : (
            <>
              <Send className="w-4 h-4 mr-2" />
              Enviar Respostas
              {answered < total && (
                <span className="ml-2 text-xs opacity-80">
                  ({total - answered} restantes)
                </span>
              )}
            </>
          )}
        </Button>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function SurveyPage() {
  const params = useParams();
  const token = params.token as string;

  const [step, setStep] = useState<Step>("loading");
  const [error, setError] = useState("");
  const [surveyData, setSurveyData] = useState<SurveyData | null>(null);
  const [gender, setGender] = useState("");
  const [ageRange, setAgeRange] = useState("");
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const validate = async () => {
      try {
        const res = await surveyApi.validate(token);
        setSurveyData(res.data);
        setStep("consent");
      } catch (err: unknown) {
        const status = (err as { response?: { status?: number; data?: { detail?: string; answered?: boolean } } })
          ?.response?.status;
        const data = (err as { response?: { data?: { detail?: string; answered?: boolean } } })
          ?.response?.data;

        if (status === 410 || data?.answered) {
          setStep("already_answered");
        } else {
          setError(data?.detail ?? "Link inválido ou expirado.");
          setStep("error");
        }
      }
    };
    validate();
  }, [token]);

  const handleAnswer = (questionId: number, value: number) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const handleSubmit = async () => {
    if (!surveyData) return;
    setSubmitting(true);
    try {
      const answersArray = Object.entries(answers).map(([qId, v]) => ({
        question_id: Number(qId),
        value: v,
      }));
      await surveyApi.submit(token, {
        consent: true,
        gender: gender || undefined,
        age_range: ageRange || undefined,
        answers: answersArray,
      });
      setStep("done");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Erro ao enviar respostas.";
      setError(msg);
      setStep("error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-purple-50 py-8 px-4">
      {/* Logo header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-white rounded-full border border-slate-200 shadow-sm">
          <div className="w-6 h-6 bg-gradient-to-br from-purple-500 to-blue-600 rounded-md" />
          <span className="font-semibold text-slate-800 text-sm">Vivamente360</span>
        </div>
      </div>

      {/* Steps */}
      {step === "loading" && (
        <div className="text-center py-16">
          <div className="w-10 h-10 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-500">Verificando link...</p>
        </div>
      )}

      {step === "error" && (
        <div className="max-w-md mx-auto text-center py-12 space-y-4">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto">
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Link Inválido</h2>
          <p className="text-slate-500">{error}</p>
        </div>
      )}

      {step === "already_answered" && (
        <div className="max-w-md mx-auto text-center py-12 space-y-4">
          <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto">
            <AlertCircle className="w-8 h-8 text-amber-500" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">
            Pesquisa já respondida
          </h2>
          <p className="text-slate-500">
            Este link já foi utilizado. Cada link pode ser usado apenas uma vez.
          </p>
        </div>
      )}

      {step === "consent" && surveyData && (
        <ConsentTerm
          campaignName={surveyData.campaign.name}
          onAccept={() => setStep("demographics")}
          onDecline={() => setStep("error")}
        />
      )}

      {step === "demographics" && (
        <DemographicsStep
          gender={gender}
          ageRange={ageRange}
          onGenderChange={setGender}
          onAgeRangeChange={setAgeRange}
          onNext={() => setStep("questions")}
        />
      )}

      {step === "questions" && surveyData && (
        <QuestionsStep
          surveyData={surveyData}
          answers={answers}
          onAnswer={handleAnswer}
          onBack={() => setStep("demographics")}
          onSubmit={handleSubmit}
          submitting={submitting}
        />
      )}

      {step === "done" && (
        <div className="max-w-md mx-auto text-center py-12 space-y-4">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-10 h-10 text-green-500" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900">
            Obrigado pela participação!
          </h2>
          <p className="text-slate-500 leading-relaxed">
            Suas respostas foram registradas de forma anônima e confidencial.
            <br />
            Elas contribuirão para melhorar o ambiente de trabalho.
          </p>
          <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 text-xs text-slate-500">
            Dados tratados em conformidade com a LGPD.
          </div>
        </div>
      )}
    </div>
  );
}
