'use client';

import { useState, useEffect } from 'react';
import { Card, CardBody, CardHeader, Button, Spinner, Chip } from "@heroui/react";
import { cacheAPI, CacheStats, CacheInfo } from '@/lib/api';

export default function CacheManager() {
  const [cacheInfo, setCacheInfo] = useState<CacheInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [clearing, setClearing] = useState(false);

  useEffect(() => {
    loadCacheInfo();
  }, []);

  const loadCacheInfo = async () => {
    setLoading(true);
    try {
      console.log('Loading cache info...');
      const info = await cacheAPI.getCacheInfo();
      console.log('Cache info loaded:', info);
      setCacheInfo(info);
    } catch (error) {
      console.error('Error loading cache info:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClearCache = async () => {
    setClearing(true);
    try {
      console.log('Attempting to clear cache...');
      const result = await cacheAPI.clearCache();
      console.log('Cache clear result:', result);
      await loadCacheInfo(); // Reload stats
      console.log('Cache info reloaded');
    } catch (error) {
      console.error('Error clearing cache:', error);
    } finally {
      setClearing(false);
    }
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardBody className="flex justify-center py-8">
          <Spinner size="lg" />
        </CardBody>
      </Card>
    );
  }

  if (!cacheInfo) {
    return (
      <Card className="w-full">
        <CardBody>
          <p className="text-gray-500">Unable to load cache information</p>
        </CardBody>
      </Card>
    );
  }

  const { cache_stats, cache_duration_hours, description } = cacheInfo;

  return (
    <Card className="w-full">
      <CardHeader className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">Cache Management</h3>
          <p className="text-sm text-gray-600">{description}</p>
        </div>
        <Button
          color="danger"
          variant="flat"
          size="sm"
          onPress={handleClearCache}
          isLoading={clearing}
          disabled={clearing}
        >
          {clearing ? 'Clearing...' : 'Clear Cache'}
        </Button>
      </CardHeader>
      <CardBody>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {cache_stats.total_files}
            </div>
            <div className="text-sm text-gray-600">Cache Files</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {cache_stats.total_size_mb} MB
            </div>
            <div className="text-sm text-gray-600">Total Size</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {cache_stats.expired_files}
            </div>
            <div className="text-sm text-gray-600">Expired Files</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {cache_duration_hours}h
            </div>
            <div className="text-sm text-gray-600">Cache Duration</div>
          </div>
        </div>
        
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-semibold text-blue-800 mb-2">Performance Benefits</h4>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Cached searches return instantly (vs 10-30 seconds for fresh scrapes)</li>
            <li>• Reduces load on job board servers</li>
            <li>• Improves user experience with faster response times</li>
            <li>• Cache automatically expires after {cache_duration_hours} hours</li>
          </ul>
        </div>
      </CardBody>
    </Card>
  );
} 