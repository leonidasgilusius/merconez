import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown, ArrowRightLeft, Type, FileText, ImageIcon, AudioLines, Sparkles, Pilcrow, BookOpen, Mic2 } from 'lucide-react';

// --- Language & Type Data ---
const languages = [
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
    { code: 'ja', name: 'Japanese' },
    { code: 'ko', name: 'Korean' },
    { code: 'hi', name: 'Hindi' },
    { code: 'zh', name: 'Chinese' },
    { code: 'ar', name: 'Arabic' },
];

const inputTypes = [
    { id: 'text', name: 'Text', icon: Type },
    { id: 'document', name: 'Document', icon: FileText },
    { id: 'image', name: 'Image', icon: ImageIcon },
    { id: 'speech', name: 'Speech', icon: Mic2 },
];

const outputTypes = [
    { id: 'translation', name: 'Translation', icon: Sparkles },
    { id: 'summary', name: 'Summary', icon: Pilcrow },
    { id: 'analysis', name: 'Analysis', icon: BookOpen },
    { id: 'audio', name: 'Audio', icon: AudioLines },
];

// --- Custom Hook for Dropdowns ---
const useDropdown = () => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const toggle = () => setIsOpen(!isOpen);
    const close = () => setIsOpen(false);

    return { isOpen, toggle, close, dropdownRef };
};

// --- Reusable Components ---
const TypeSelector = ({ types, selected, onSelect, title }) => (
    <div className="w-full">
        <label className="text-sm font-medium text-slate-300">{title}</label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-2">
            {types.map(type => (
                <button
                    key={type.id}
                    onClick={() => onSelect(type)}
                    className={`flex flex-col items-center justify-center p-3 rounded-lg border-2 transition-all duration-300 ${
                        selected.id === type.id
                            ? 'bg-sky-500 border-sky-400 text-white shadow-lg shadow-sky-500/30'
                            : 'bg-slate-700/50 border-slate-600 hover:bg-slate-700 hover:border-slate-500 text-slate-300'
                    }`}
                >
                    <type.icon className="w-6 h-6 mb-1" />
                    <span className="text-xs font-semibold">{type.name}</span>
                </button>
            ))}
        </div>
    </div>
);

const LanguageSelector = ({ selected, onSelect, title }) => {
    const { isOpen, toggle, close, dropdownRef } = useDropdown();

    return (
        <div className="relative w-full" ref={dropdownRef}>
            <label className="text-sm font-medium text-slate-300">{title}</label>
            <button
                onClick={toggle}
                className="flex items-center justify-between w-full p-3 mt-2 bg-slate-700/50 border-2 border-slate-600 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
                <span>{selected.name}</span>
                <ChevronDown className={`w-5 h-5 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} />
            </button>
            {isOpen && (
                <div className="absolute z-10 w-full mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl max-h-48 overflow-y-auto animate-fade-in-down">
                    {languages.map(lang => (
                        <div
                            key={lang.code}
                            onClick={() => {
                                onSelect(lang);
                                close();
                            }}
                            className="p-3 text-sm text-slate-300 hover:bg-sky-500 hover:text-white cursor-pointer"
                        >
                            {lang.name}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

// --- Main App Component ---
export default function App() {
    const [inputType, setInputType] = useState(inputTypes[0]);
    const [outputType, setOutputType] = useState(outputTypes[0]);
    const [inputLang, setInputLang] = useState(languages[0]);
    const [outputLang, setOutputLang] = useState(languages[1]);
    const [inputText, setInputText] = useState('');
    const [outputText, setOutputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSwapLanguages = () => {
        const tempLang = inputLang;
        setInputLang(outputLang);
        setOutputLang(tempLang);
    };
    
    // Remember to install lucide-react for the icons
    // In your terminal run: npm install lucide-react

    const handleProcess = () => {
        if (!inputText.trim()) {
            setError('Please enter some text to process.');
            return;
        }
        setError('');
        setIsLoading(true);
        setOutputText('');

        // Mock API call
        setTimeout(() => {
            setOutputText(`Processed "${inputText}" from ${inputLang.name} (${inputType.name}) to ${outputLang.name} (${outputType.name}).`);
            setIsLoading(false);
        }, 1500);
    };

    return (
        <div className="min-h-screen w-full bg-slate-900 text-white font-sans flex items-center justify-center p-4 bg-grid-slate-800/50">
            <style>{`
                @keyframes fade-in { 0% { opacity: 0; transform: translateY(-10px); } 100% { opacity: 1; transform: translateY(0); } }
                @keyframes fade-in-down { 0% { opacity: 0; transform: translateY(-5px); } 100% { opacity: 1; transform: translateY(0); } }
                .animate-fade-in { animation: fade-in 0.5s ease-out forwards; }
                .animate-fade-in-down { animation: fade-in-down 0.3s ease-out forwards; }
                .bg-grid-slate-800\\/50 { background-image: linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px); background-size: 20px 20px; }
            `}</style>
            
            <div className="w-full max-w-2xl mx-auto bg-slate-800/50 backdrop-blur-xl border border-slate-700 rounded-2xl shadow-2xl shadow-black/30 p-6 md:p-8 animate-fade-in">
                <header className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-blue-500">Universal Transformer</h1>
                    <p className="text-slate-400 mt-1">Your AI-powered content processor.</p>
                </header>

                <main className="space-y-6">
                    {/* Input Section */}
                    <div className="space-y-4">
                        <TypeSelector types={inputTypes} selected={inputType} onSelect={setInputType} title="Input Type" />
                        <div className="flex flex-col md:flex-row items-center gap-4">
                            <LanguageSelector selected={inputLang} onSelect={setInputLang} title="Input Language" />
                             <button 
                                onClick={handleSwapLanguages}
                                className="p-3 mt-auto bg-slate-700/50 border-2 border-slate-600 rounded-lg text-slate-300 hover:bg-slate-700 hover:text-sky-400 transition-colors duration-300"
                                aria-label="Swap Languages"
                            >
                                <ArrowRightLeft className="w-5 h-5" />
                            </button>
                            <LanguageSelector selected={outputLang} onSelect={setOutputLang} title="Output Language" />
                        </div>
                        <textarea
                            value={inputText}
                            onChange={(e) => setInputText(e.target.value)}
                            placeholder={`Enter ${inputLang.name} ${inputType.name.toLowerCase()} here...`}
                            className="w-full h-32 p-3 bg-slate-700/50 border-2 border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 transition-colors duration-300 placeholder-slate-500"
                        />
                         {error && <p className="text-red-400 text-sm mt-1">{error}</p>}
                    </div>

                    {/* Action Button */}
                    <button
                        onClick={handleProcess}
                        disabled={isLoading}
                        className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-sky-500 to-blue-600 text-white font-bold py-3 px-4 rounded-lg shadow-lg hover:shadow-sky-500/40 transform hover:-translate-y-0.5 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isLoading ? (
                           <>
                                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                <span>Processing...</span>
                           </>
                        ) : (
                           <span>Process Content</span>
                        )}
                    </button>

                    {/* Output Section */}
                     <div className="space-y-4">
                        <TypeSelector types={outputTypes} selected={outputType} onSelect={setOutputType} title="Output Type" />
                        <div className="w-full min-h-[8rem] p-3 bg-slate-900/70 border-2 border-slate-700 rounded-lg">
                           <p className="text-slate-300">{outputText || 'Output will appear here...'}</p>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}

