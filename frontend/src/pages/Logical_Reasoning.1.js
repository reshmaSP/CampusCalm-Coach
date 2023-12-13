import React, { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import { NavLink } from "react-router-dom";
import "./Logical_Reasoning.css";

const categories = [
  "Analogies",
  "Analyzing_Arguments",
  "Artificial_Language",
  "Essential_Part",
  "Letter_And_Symbol_Series",
  "Logical_Games",
  "Logical_Problems",
  "Making_Judgements",
  "Number_Series",
  "Statement_And_Assumption",
  "Verbal_Classification",
  "Verbal_Reasoning",
];

const LogicalReasoning = () => {
  const [questions, setQuestions] = useState({});
  const [userAnswers, setUserAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [showResults, setShowResults] = useState(false);
  const [score, setScore] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      const fetchedQuestions = {};

      for (const category of categories) {
        const response = await fetch(`/Logical_Reasoning/${category}.json`);
        const data = await response.json();
        const shuffledQuestions = [...data].sort(() => Math.random() - 0.5);
        const selectedQuestions = shuffledQuestions.slice(0, 2);
        fetchedQuestions[category] = selectedQuestions;
        const questionsWithAnswers = selectedQuestions.map((question) => ({
          ...question,
          answer: question.answer, 
        }));
        fetchedQuestions[category] = questionsWithAnswers;
      }

      setQuestions(fetchedQuestions);
    };

    fetchData();
  }, []);

  const handleAnswerSelection = (category, questionIndex, selectedOption) => {
    setUserAnswers((prevAnswers) => ({
      ...prevAnswers,
      [category]: {
        ...prevAnswers[category],
        [questionIndex]: selectedOption,
      },
    }));
  };

  const calculateScore = () => {
    let calculatedScore = 0;
    console.log(userAnswers);
    for (const category in userAnswers) {
      for (const questionIndex in userAnswers[category]) {
        const selectedOption = userAnswers[category][questionIndex];
        const correctAnswer = questions[category][questionIndex].answer;
        console.log(`Category: ${category}, Question: ${questionIndex}`);
      console.log(`Selected Option: ${selectedOption}`);
      console.log(`Correct Answer: ${correctAnswer}`);

      const optionIndex = questions[category][questionIndex].options.indexOf(selectedOption);
      const correctAnswerChar = String.fromCharCode(97 + optionIndex); // 'a' corresponds to 97 in ASCII

      if (correctAnswerChar === correctAnswer) {
        calculatedScore++;
      }
      }
    }
    setScore(calculatedScore);
    setShowResults(true);
    sessionStorage.setItem("LR_Score",calculatedScore);
	 calculatedScore = calculatedScore*100
	  calculatedScore = calculatedScore/24
    sessionStorage.setItem("LR_Score",parseInt(calculatedScore));
          
  };
  
  return (
    <>
      <Navbar />
      <div id="container">
        <h1 id="Header">Logical Reasoning Test</h1>
        {categories.map((category) => (
          <div key={category}>
            <h2 className="section-title">{category}</h2>
            {questions[category] &&
              questions[category].map((question, index) => (
                <div key={index}>
                  <h3 className="question-title">Question {index + 1}:</h3>
                  <p className="question-text">{question.question}</p>
                  <ul className="answer-options"          >
                    {question.options.map((option, optionIndex) => (
                        <label>
                          <input
                            type="radio"
                            name={`${category}-${index}`}
                            value={option}
                            className="answer-option"
                            onChange={() =>
                              handleAnswerSelection(category, index, option)
                            }
                            disabled={showResults}
                          />
                          {option}
                        <p>{question.answer}</p>  
                        </label>
                        
                    ))}
                  </ul>
                </div>
              ))}
          </div>
        ))}
        {showResults ? (
          <div className='btdiv'><NavLink to='/user/career_test/arithmetic_reasoning'><button type='submit' className='startButton'>Go to next Assesment</button></NavLink></div>
        ) : (
          // <button onClick={calculateScore}>Submit Test</button>
          <div className='btdiv'><button className='startButton' onClick={calculateScore}>Submit Test</button></div>
        )}
      </div>
      <Footer />
    </>
  );
};

export default LogicalReasoning;
