'use client';

import { useAudioStream } from '@/hooks/useAudioStream';

export default function Home() {
  // We'll connect to a local backend for now
  const { isRecording, startRecording, stopRecording, transcript, actionItems } = 
    useAudioStream('ws://localhost:8000/ws/meeting');

  return (
    <main className="min-h-screen bg-gray-50 p-8 text-gray-900">
      <header className="mb-8 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <h1 className="text-3xl font-bold text-blue-600">MeetingBrain</h1>
          
          {/* The Pulsing Recording Indicator */}
          {isRecording && (
            <div className="flex items-center gap-2 px-3 py-1 bg-red-50 rounded-full border border-red-100">
              <span className="relative flex h-3 w-3">
                {/* The pinging background layer */}
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                {/* The solid core dot */}
                <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
              </span>
              <span className="text-sm font-medium text-red-600 animate-pulse">
                Recording
              </span>
            </div>
          )}
        </div>

        <button 
          onClick={isRecording ? stopRecording : startRecording}
          className={`px-6 py-3 rounded-full font-semibold text-white transition-colors shadow-sm ${
            isRecording 
              ? 'bg-red-500 hover:bg-red-600 focus:ring-4 focus:ring-red-200' 
              : 'bg-green-500 hover:bg-green-600 focus:ring-4 focus:ring-green-200'
          }`}
        >
          {isRecording ? 'Stop Meeting' : 'Start Meeting'}
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 h-[80vh]">
        {/* Left Column: Live Transcript */}
        <section className="col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col">
          <h2 className="text-xl font-semibold border-b pb-4 mb-4">Live Transcript</h2>
          <div className="flex-1 overflow-y-auto font-mono text-sm text-gray-700 whitespace-pre-wrap">
            {transcript || "Waiting for conversation to start..."}
          </div>
        </section>

        {/* Right Column: AI Action Items */}
        <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col">
          <h2 className="text-xl font-semibold border-b pb-4 mb-4 text-indigo-600">Action Items</h2>
          <div className="flex-1 overflow-y-auto space-y-4">
            {actionItems.length === 0 ? (
              <p className="text-gray-400 italic text-sm">Listening for tasks...</p>
            ) : (
              actionItems.map((item, idx) => (
                <div key={idx} className="p-4 bg-indigo-50 rounded-lg border border-indigo-100">
                  <h3 className="font-bold text-indigo-900">{item.title}</h3>
                  <p className="text-sm text-indigo-700 mt-1">{item.assignee} - {item.deadline}</p>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </main>
  );
}