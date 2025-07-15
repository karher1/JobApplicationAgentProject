'use client';

import { useState, useEffect } from 'react';
import { jobSearchAPI } from '@/lib/api';

interface CompanySelectorProps {
  selectedCompanies: string[];
  onCompaniesChange: (companies: string[]) => void;
  maxCompanies?: number;
}

interface CompanyDomains {
  [domain: string]: string[];
}

// Pretty display names for companies
const COMPANY_DISPLAY_NAMES: { [key: string]: string } = {
  // Generative AI
  'openai': 'OpenAI',
  'anthropic': 'Anthropic',
  'cohere': 'Cohere',
  'mistral-ai': 'Mistral AI',
  'inflection-ai': 'Inflection AI',
  'xai': 'xAI',
  'adept': 'Adept',
  'perplexity-ai': 'Perplexity AI',
  'runway': 'Runway',
  'hugging-face': 'Hugging Face',
  'stability-ai': 'Stability AI',
  
  // AI Infrastructure / Tooling
  'pinecone': 'Pinecone',
  'weaviate': 'Weaviate',
  'langchain': 'LangChain',
  'weights-biases': 'Weights & Biases',
  'scale-ai': 'Scale AI',
  'labelbox': 'Labelbox',
  'truera': 'TruEra',
  
  // Enterprise AI Platforms
  'databricks': 'Databricks',
  'datarobot': 'DataRobot',
  'c3-ai': 'C3.ai',
  'abacus-ai': 'Abacus.AI',
  'sambanova': 'SambaNova',
  
  // Cloud / Infrastructure
  'amazon': 'Amazon',
  'microsoft': 'Microsoft',
  'google': 'Google',
  'cloudflare': 'Cloudflare',
  'digitalocean': 'DigitalOcean',
  'fastly': 'Fastly',
  
  // Developer Platforms
  'github': 'GitHub',
  'gitlab': 'GitLab',
  'hashicorp': 'HashiCorp',
  'circleci': 'CircleCI',
  'netlify': 'Netlify',
  'vercel': 'Vercel',
  'render': 'Render',
  'replit': 'Replit',
  
  // Dev Tools & SaaS
  'atlassian': 'Atlassian',
  'linear': 'Linear',
  'notion': 'Notion',
  'slack': 'Slack',
  'figma': 'Figma',
  'retool': 'Retool',
  'clickup': 'ClickUp',
  
  // Consumer & Social Tech
  'apple': 'Apple',
  'meta': 'Meta',
  'snap': 'Snap Inc.',
  'bytedance': 'ByteDance',
  'spotify': 'Spotify',
  'netflix': 'Netflix',
  'pinterest': 'Pinterest',
  
  // Fintech
  'stripe': 'Stripe',
  'square': 'Square',
  'plaid': 'Plaid',
  'brex': 'Brex',
  'ramp': 'Ramp',
  'affirm': 'Affirm',
  'robinhood': 'Robinhood',
  'chime': 'Chime',
  'coinbase': 'Coinbase',
  
  // Analytics & Data
  'snowflake': 'Snowflake',
  'confluent': 'Confluent',
  'segment': 'Segment',
  'mixpanel': 'Mixpanel',
  'amplitude': 'Amplitude',
  'looker': 'Looker',
  'tableau': 'Tableau',
  
  // Security
  'okta': 'Okta',
  'auth0': 'Auth0',
  'crowdstrike': 'CrowdStrike',
  'sentinelone': 'SentinelOne',
  'snyk': 'Snyk',
  
  // Enterprise SaaS
  'salesforce': 'Salesforce',
  'workday': 'Workday',
  'servicenow': 'ServiceNow',
  'zendesk': 'Zendesk',
  'box': 'Box',
  'dropbox': 'Dropbox',
  'zoom': 'Zoom',
};

// Popular companies for quick selection
const POPULAR_COMPANIES = [
  'google', 'amazon', 'apple', 'meta', 'microsoft', 'netflix', 'tesla', 'nvidia',
  'openai', 'anthropic', 'stripe', 'coinbase', 'github', 'figma', 'notion', 'linear'
];

export default function CompanySelector({ 
  selectedCompanies, 
  onCompaniesChange, 
  maxCompanies = 5 
}: CompanySelectorProps) {
  const [domains, setDomains] = useState<CompanyDomains>({});
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedDomain, setSelectedDomain] = useState<string>('');

  useEffect(() => {
    loadCompanyDomains();
  }, []);

  const loadCompanyDomains = async () => {
    try {
      setLoading(true);
      const response = await jobSearchAPI.getCompanyDomains();
      setDomains((response && typeof response === 'object') ? response : {});
    } catch (error) {
      console.error('Error loading company domains:', error);
      setDomains({});
    } finally {
      setLoading(false);
    }
  };

  const handleCompanyToggle = (company: string) => {
    const newSelectedCompanies = [...selectedCompanies];
    const companyIndex = newSelectedCompanies.indexOf(company);
    
    if (companyIndex > -1) {
      // Remove company
      newSelectedCompanies.splice(companyIndex, 1);
    } else {
      // Add company (if under limit)
      if (newSelectedCompanies.length < maxCompanies) {
        newSelectedCompanies.push(company);
      }
    }
    
    onCompaniesChange(newSelectedCompanies);
  };

  const removeCompany = (company: string) => {
    const newSelectedCompanies = selectedCompanies.filter(c => c !== company);
    onCompaniesChange(newSelectedCompanies);
  };

  const isCompanySelected = (company: string) => {
    return selectedCompanies.includes(company);
  };

  const getDisplayName = (companyKey: string): string => {
    return COMPANY_DISPLAY_NAMES[companyKey] || companyKey.charAt(0).toUpperCase() + companyKey.slice(1);
  };

  // Get all companies from all domains
  const getAllCompanies = () => {
    const allCompanies: string[] = [];
    Object.values(domains).forEach(companies => {
      allCompanies.push(...companies);
    });
    return [...new Set(allCompanies)]; // Remove duplicates
  };

  // Filter companies based on search term
  const getFilteredCompanies = () => {
    if (!searchTerm) return [];
    
    const allCompanies = getAllCompanies();
    return allCompanies.filter(company => 
      getDisplayName(company).toLowerCase().includes(searchTerm.toLowerCase()) ||
      company.toLowerCase().includes(searchTerm.toLowerCase())
    ).slice(0, 10); // Limit to 10 results
  };

  // Get companies for selected domain
  const getDomainCompanies = () => {
    if (!selectedDomain || !domains[selectedDomain]) return [];
    return domains[selectedDomain];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading companies...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Selected Companies Display */}
      {selectedCompanies.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Selected ({selectedCompanies.length}/{maxCompanies})
            </span>
            <button
              onClick={() => onCompaniesChange([])}
              className="text-xs text-red-600 hover:text-red-700 font-medium"
            >
              Clear all
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedCompanies.map((company) => (
              <div
                key={company}
                className="flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-lg text-sm font-medium"
              >
                <span>{getDisplayName(company)}</span>
                <button
                  onClick={() => removeCompany(company)}
                  className="text-blue-600 hover:text-blue-800 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Popular Companies Quick Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Popular Companies
        </label>
        <div className="flex flex-wrap gap-2">
          {POPULAR_COMPANIES.map((company) => (
            <button
              key={company}
              onClick={() => handleCompanyToggle(company)}
              disabled={!isCompanySelected(company) && selectedCompanies.length >= maxCompanies}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-all duration-200 ${
                isCompanySelected(company)
                  ? 'bg-blue-600 text-white shadow-md'
                  : selectedCompanies.length >= maxCompanies
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-gray-100 text-gray-700 hover:bg-blue-50 hover:text-blue-700 hover:shadow-sm'
              }`}
            >
              {getDisplayName(company)}
            </button>
          ))}
        </div>
      </div>

      {/* Search Companies */}
      <div className="relative">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Search Companies
        </label>
        <div className="relative">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onFocus={() => setShowDropdown(true)}
            onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
            className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
            placeholder="Type to search companies..."
          />
          <div className="absolute right-3 top-2.5 text-gray-400">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>
        
        {/* Search Results Dropdown */}
        {showDropdown && searchTerm && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
            {getFilteredCompanies().length > 0 ? (
              getFilteredCompanies().map((company) => (
                <button
                  key={company}
                  onClick={() => {
                    handleCompanyToggle(company);
                    setSearchTerm('');
                  }}
                  disabled={!isCompanySelected(company) && selectedCompanies.length >= maxCompanies}
                  className={`w-full px-4 py-2 text-left transition-colors duration-150 first:rounded-t-lg last:rounded-b-lg ${
                    isCompanySelected(company)
                      ? 'bg-blue-50 text-blue-700 font-medium'
                      : selectedCompanies.length >= maxCompanies
                        ? 'text-gray-400 cursor-not-allowed'
                        : 'hover:bg-gray-50 text-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span>{getDisplayName(company)}</span>
                    {isCompanySelected(company) && (
                      <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                </button>
              ))
            ) : (
              <div className="px-4 py-2 text-gray-500 text-sm">
                No companies found matching "{searchTerm}"
              </div>
            )}
          </div>
        )}
      </div>

      {/* Browse by Domain */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Browse by Category
        </label>
        <select
          value={selectedDomain}
          onChange={(e) => setSelectedDomain(e.target.value)}
          className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
        >
          <option value="">Select a category...</option>
          {Object.keys(domains).map((domain) => (
            <option key={domain} value={domain}>
              {domain} ({domains[domain].length} companies)
            </option>
          ))}
        </select>
      </div>

      {/* Companies in Selected Domain */}
      {selectedDomain && getDomainCompanies().length > 0 && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Companies in {selectedDomain}
          </label>
          <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
            {getDomainCompanies().map((company) => (
              <button
                key={company}
                onClick={() => handleCompanyToggle(company)}
                disabled={!isCompanySelected(company) && selectedCompanies.length >= maxCompanies}
                className={`px-3 py-2 text-sm rounded-lg border transition-all duration-200 text-left ${
                  isCompanySelected(company)
                    ? 'bg-blue-600 text-white border-blue-700 shadow-md'
                    : selectedCompanies.length >= maxCompanies
                      ? 'bg-gray-50 text-gray-400 border-gray-200 cursor-not-allowed'
                      : 'bg-white text-gray-700 border-gray-200 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="truncate">{getDisplayName(company)}</span>
                  {isCompanySelected(company) && (
                    <svg className="w-4 h-4 ml-1 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Helper Text */}
      {selectedCompanies.length >= maxCompanies && (
        <div className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg p-3">
          <div className="flex items-center">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            Maximum {maxCompanies} companies reached. Remove some to add more.
          </div>
        </div>
      )}
    </div>
  );
} 