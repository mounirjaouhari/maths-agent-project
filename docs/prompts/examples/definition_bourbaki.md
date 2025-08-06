# Exemple de Prompt : Définition Formelle (Style Bourbaki)

Ce prompt est un exemple de ce qui serait envoyé à un LLM par le Service Génération pour obtenir une définition formelle dans le style "Bourbaki". Il est basé sur le template `definition` avec le style `Bourbaki` de `templates.yaml`.

---

Tu es un assistant de rédaction de manuel de mathématiques expert, spécialisé dans la production de définitions formelles et rigoureuses, dans le style de Bourbaki.

**Instructions:**
1. Fournis uniquement la définition formelle du concept spécifié.
2. Utilise exclusivement la notation LaTeX pour toutes les expressions et symboles mathématiques.
3. Assure-toi que la définition est complète et sans ambiguïté pour le niveau spécifié.
4. Ne pas inclure d'explications intuitives, d'exemples, de commentaires ou de texte introductif/conclusif.
5. Commence ta réponse directement par le code LaTeX de la définition.

**Concept à définir:** Espace Vectoriel
**Niveau de rigueur (correspondant au niveau cible):** L2
**Définition formelle de référence (issue de la KB, si disponible):**
```latex
Soit $E$ un ensemble non vide, muni d'une loi de composition interne, notée $+$, et d'une loi de composition externe, notée $\cdot$, à valeurs dans un corps $\mathbb{K}$. On dit que $(E, +, \cdot)$ est un $\mathbb{K}$-espace vectoriel si...

Contexte: Ce concept est introduit après les notions de corps, de groupes et d'anneaux.

Format de sortie attendu: Code LaTeX pur.
Définition formelle:

% Le LLM générerait ici la définition formelle complète de l'espace vectoriel en LaTeX,
% en s'appuyant sur les instructions et la définition de référence.
% Exemple de sortie attendue:
\documentclass{article}
\usepackage{amsmath}
\begin{document}

\textbf{Définition (Espace Vectoriel).} Soit $E$ un ensemble non vide. On munit $E$ d'une loi de composition interne, notée $+$ (addition), et d'une loi de composition externe, notée $\cdot$ (multiplication par un scalaire), à valeurs dans un corps $\mathbb{K}$.
L'ensemble $E$ est appelé un \textbf{$\mathbb{K}$-espace vectoriel} si les propriétés suivantes sont vérifiées :
\begin{enumerate}
    \item Pour tout $u, v \in E$, $u+v \in E$ (stabilité de l'addition).
    \item Pour tout $u, v, w \in E$, $(u+v)+w = u+(v+w)$ (associativité de l'addition).
    \item Il existe un élément $0_E \in E$ tel que pour tout $u \in E$, $u+0_E = u$ (existence d'un élément neutre pour l'addition).
    \item Pour tout $u \in E$, il existe un élément $-u \in E$ tel que $u+(-u) = 0_E$ (existence d'un opposé pour l'addition).
    \item Pour tout $u, v \in E$, $u+v = v+u$ (commutativité de l'addition).
    \item Pour tout $\lambda \in \mathbb{K}$ et tout $u \in E$, $\lambda \cdot u \in E$ (stabilité de la multiplication par un scalaire).
    \item Pour tout $\lambda \in \mathbb{K}$ et tout $u, v \in E$, $\lambda \cdot (u+v) = \lambda \cdot u + \lambda \cdot v$ (distributivité de la multiplication par un scalaire sur l'addition des vecteurs).
    \item Pour tout $\lambda, \mu \in \mathbb{K}$ et tout $u \in E$, $(\lambda+\mu) \cdot u = \lambda \cdot u + \mu \cdot u$ (distributivité de la multiplication par un scalaire sur l'addition des scalaires).
    \item Pour tout $\lambda, \mu \in \mathbb{K}$ et tout $u \in E$, $\lambda \cdot (\mu \cdot u) = (\lambda\mu) \cdot u$ (associativité mixte).
    \item Pour tout $u \in E$, $1_{\mathbb{K}} \cdot u = u$, où $1_{\mathbb{K}}$ est l'élément neutre de la multiplication dans $\mathbb{K}$ (action du scalaire unité).
\end{enumerate}

\end{document}
