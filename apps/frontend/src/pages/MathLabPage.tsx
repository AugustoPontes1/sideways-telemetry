import { BookOpen, GraduationCap, Lightbulb } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { EmptyState } from '../components/EmptyState';
import { PageTitle } from '../components/PageTitle';
import { Panel } from '../components/Panel';
import { MathExercise } from '../modules/math-lab/MathExercise';

export function MathLabPage() {
  const { samples, activeSession, demo } = useApp();
  return <>
    <PageTitle eyebrow="MÓDULOS / ÁLGEBRA LINEAR" title="Laboratório matemático"
      subtitle="Use os valores da sua pilotagem como exercícios. Veja o resultado, resolva à mão e revele a explicação somente depois."/>
    {!activeSession || samples.length < 2 ? <EmptyState title="Precisamos de pelo menos duas amostras"/> : <>
      <div className="math-intro">
        <span className="intro-icon"><GraduationCap size={23}/></span>
        <div><strong>Aprender fazendo</strong><p>O resultado final fica visível; o processo e a escolha da propriedade permanecem ocultos até você solicitar.</p></div>
        <BookOpen className="intro-watermark" size={52}/>
      </div>
      <div className="content-grid math-grid">
        <Panel title="Exercício com telemetria" subtitle="Selecione um tema e dois instantes da sessão">
          <MathExercise streamId={activeSession.stream_id} samples={samples} demo={demo}/>
        </Panel>
        <Panel title="Como estudar com os dados" subtitle="Método de aprendizagem sugerido">
          <div className="study-steps">
            <div><span>01</span><p>Observe os valores reais ou simulados e entenda o que precisa calcular.</p></div>
            <div><span>02</span><p>Identifique o conceito matemático adequado antes de consultar as fórmulas.</p></div>
            <div><span>03</span><p>Resolva no papel, confira o resultado e revise as propriedades utilizadas.</p></div>
            <div><span>04</span><p>Revele a solução completa somente quando quiser comparar seu raciocínio.</p></div>
          </div>
          <div className="learning-note"><Lightbulb size={20}/><p>Este MVP oferece oito tipos de exercícios no backend. Não representa automaticamente todas as aulas da disciplina.</p></div>
        </Panel>
      </div>
    </>}
  </>;
}
